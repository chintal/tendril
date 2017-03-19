#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Base project configuration structures.

Files :
    - Config File
    - Project Folder
    - Documentation Folder
    - Pricing Folder (Deprecate?)

Project Structures:
    - Groups
    - Motifs
    - Generators
    - Jumpers

Configuration Tree:
    - Config Sections
    - Config Matrix
    - Configurations

Specialized Structures:
    - Description
    - Status
    - Serial Number Series
    - Production Information *
    - Documentation Information *
    - Testing Information
        - tests
        - testvars

"""

import os
import copy
import itertools
import warnings
from decimal import Decimal

from tendril.boms.validate import ValidationContext
from tendril.boms.validate import ErrorCollector
from tendril.boms.validate import ValidationError
from tendril.boms.validate import ValidationPolicy
from tendril.boms.validate import ConfigOptionPolicy

from tendril.boms.validate import get_dict_val

from tendril.utils.files import yml as yaml
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class NoProjectError(Exception):
    pass


class SchemaPolicy(ValidationPolicy):
    def __init__(self, context, name, vmax, vmin):
        super(SchemaPolicy, self).__init__(context)
        self.name = name
        self.vmax = vmax
        self.vmin = vmin

    def validate(self, name, version):
        if name == self.name and self.vmin <= version <= self.vmax:
            return True
        else:
            return False


class SchemaNotSupportedError(ValidationError):
    def __init__(self, policy, value):
        super(SchemaNotSupportedError, self).__init__(policy)
        self._value = value

    def __repr__(self):
        return "<SchemaNotSupportedError {0}{1}>" \
               "".format(self._policy.context, self._value)


class ConfigBase(object):
    NoProjectErrorType = NoProjectError
    schema_name = None
    schema_version_max = None
    schema_version_min = None

    def __init__(self, projectfolder):
        self._projectfolder = os.path.normpath(projectfolder)
        self._validation_context = ValidationContext(self.projectfolder,
                                                     locality='Configs')
        self._validation_errors = ErrorCollector()
        try:
            self._configdata = self.get_configs_file()
        except IOError:
            raise self.NoProjectErrorType(self._projectfolder)

    @property
    def _cfpath(self):
        raise NotImplementedError

    def get_configs_file(self):
        configdata = yaml.load(self._cfpath)
        try:
            return self._verify_schema_decl(configdata)
        except SchemaNotSupportedError as e:
            self._validation_errors.add(e)

    @property
    def _schema_name_policy(self):
        return ConfigOptionPolicy(
            self._validation_context, ('schema', 'name')
        )

    @property
    def _schema_ver_policy(self):
        return ConfigOptionPolicy(
            self._validation_context, ('schema', 'version')
        )

    def _verify_schema_decl(self, configdata):
        schema_policy = SchemaPolicy(
            self._validation_context, self.schema_name,
            self.schema_version_max, self.schema_version_min
        )
        schema_name = get_dict_val(configdata, self._schema_name_policy)
        schema_version = Decimal(get_dict_val(configdata, self._schema_ver_policy))
        if schema_policy.validate(schema_name, schema_version):
            return configdata
        else:
            raise SchemaNotSupportedError(
                schema_policy, '{0}v{1}'.format(schema_name, schema_version)
            )

    def validate(self):
        raise NotImplementedError

    @property
    def projectfolder(self):
        return self._projectfolder

    @property
    def docfolder(self):
        raise NotImplementedError

    @property
    def pricingfolder(self):
        raise NotImplementedError

    @property
    def indicative_pricing_folder(self):
        warnings.warn("Deprecated Access of indicative_pricing_folder",
                      DeprecationWarning)
        return self.pricingfolder

    @property
    def grouplist(self):
        if "grouplist" in self._configdata.keys():
            return self._configdata["grouplist"]
        else:
            return [{'name': 'default', 'desc': 'Unclassified'}]

    @property
    def file_groups(self):
        rval = {}
        # TODO Verify file names are correct
        for group in self.grouplist:
            if 'file' in group.keys():
                if isinstance(group['file'], list):
                    for f in group['file']:
                        rval[f] = group['name']
                else:
                    rval[group['file']] = group['name']
        return rval

    @property
    def group_names(self):
        return [x['name'] for x in self.grouplist]

    def get_group_desc(self, groupname):
        for group in self.grouplist:
            if group['name'] == groupname:
                return group['desc']

    @property
    def motiflist(self):
        if "motiflist" in self._configdata.keys():
            return self._configdata["motiflist"]
        else:
            return []

    @property
    def motif_refdeslist(self):
        return self.motiflist.keys()

    def motif_baseconf(self, refdes):
        for mrefdes, mconf in self.motiflist.iteritems():
            if mrefdes == refdes:
                return mconf
        raise ValueError("Motif with refdes {0} not defined for {1}"
                         "".format(refdes, self._projectfolder))

    @property
    def sjlist(self):
        if "sjlist" in self._configdata.keys():
            return self._configdata["sjlist"]
        else:
            return {}

    @property
    def genlist(self):
        raise NotImplementedError

    # Configmatrices #
    @property
    def configmatrices(self):
        if "configmatrix" in self._configdata.keys():
            return self._configdata["configmatrix"]
        else:
            return []

    def _configmatrix_baseconfigs(self):
        return [x['baseconfig'] for x in self.configmatrices]

    def _get_configmatrix(self, baseconfig):
        for configmatrix in self.configmatrices:
            if configmatrix['baseconfig'] == baseconfig:
                return configmatrix
        raise ValueError("No configmatrix uses {0} as a baseconfig for {1}"
                         "".format(baseconfig, self._projectfolder))

    def _expand_configmatrix(self, baseconfig):
        matrix = self._get_configmatrix(baseconfig['configname'])
        dimensions = {d['name']: d['options'] for d in matrix['dimensions']}
        rval = []
        for subconfig in matrix['subconfigs']:
            ldimensions = []
            laxes = []
            lactions = subconfig['actions']
            for dimension, options in dimensions.iteritems():
                if dimension in subconfig['dimensions']:
                    ldimensions.append(dimension)
                    laxes.append(options)
            for vector in itertools.product(*laxes):
                nconfig = copy.deepcopy(baseconfig)
                nconfig['configname'] = subconfig['configname']
                nconfig['desc'] = subconfig['desc']
                for idx, component in enumerate(vector):
                    dimname = ldimensions[idx]

                    # Update configname
                    nconfig['configname'] = nconfig['configname'].replace(
                            '<{0}:{1}>'.format(dimname, 'npart'),
                            component['npart']
                    )

                    # Update desc
                    nconfig['desc'] = nconfig['desc'].replace(
                            '<{0}:{1}>'.format(dimname, 'tpart'),
                            component['tpart']
                    )
                    # Update all others
                    for param, action in lactions.iteritems():
                        if action == 'pass':
                            continue
                        if action == 'extend':
                            if param == 'grouplist':
                                if param not in nconfig.keys():
                                    nconfig[param] = []
                                if param not in component.keys():
                                    # TODO Consider a valdation warning here
                                    continue
                                nlist = [x for x in component[param]
                                         if x is not None]
                                nconfig[param].extend(nlist)
                                continue
                        if action == 'update':
                            if param in ['genlist', 'sjlist']:
                                if param not in nconfig.keys():
                                    nconfig[param] = {}
                                if param not in component.keys():
                                    # TODO Consider a valdation warning here
                                    continue
                                nconfig[param].update(component[param])
                                continue
                        raise AttributeError("{0} Action not recognized for "
                                             "{1} {2}".format(
                                                action, param,
                                                self._projectfolder))
                rval.append(nconfig)
        return rval

    # Configsections #
    @property
    def configsections(self):
        if "configsections" in self._configdata.keys():
            return self._configdata["configsections"]
        else:
            return []

    @property
    def configsection_names(self):
        return [x['sectionname'] for x in self.configsections]

    def get_configsections(self):
        warnings.warn("Deprecated access of get_configsections",
                      DeprecationWarning)
        return self.configsection_names

    def configsection(self, sectionname):
        for configsection in self.configsections:
            if configsection['sectionname'] == sectionname:
                return configsection
        raise ValueError('Configsection {0} not found for {1}'
                         ''.format(sectionname, self._projectfolder))

    def configsection_groups(self, sectionname):
        return self.configsection(sectionname)['grouplist']

    def configsection_configs(self, sectionname):
        return self.configsection(sectionname)['configurations']

    def configsection_config(self, sectionname, configname):
        for config in self.configsection_configs(sectionname):
            if config['configname'] == configname:
                return config
        raise ValueError(
                'Config {0} not found for section {1} for {2}'
                ''.format(configname, sectionname, self._projectfolder)
        )

    def configsection_configgroups(self, sectionname, configname):
        return self.configsection_config(sectionname, configname)['groups']

    def get_sec_groups(self, sectionname, config):
        warnings.warn("Deprecated access of get_sec_groups",
                      DeprecationWarning)
        return self.configsection_configgroups(sectionname, config)

    # Configurations #
    @property
    def configurations(self):
        if 'configurations' not in self._configdata.keys():
            raise AttributeError("No configuration defined for {0}"
                                 "".format(self._projectfolder))
        configurations = self._configdata['configurations']
        rval = []
        for configuration in configurations:
            if configuration['configname'] in self._configmatrix_baseconfigs():  # noqa
                rval.extend(self._expand_configmatrix(configuration))
            else:
                rval.append(configuration)
        return rval

    @property
    def configuration_names(self):
        return [x['configname'] for x in self.configurations]

    def get_configurations(self):
        warnings.warn("Deprecated access of get_configurations",
                      DeprecationWarning)
        return self.configuration_names

    def configuration(self, configname):
        for x in self.configurations:
            if x['configname'] == configname:
                return x
        raise ValueError(configname + ' Not Found')

    def _configuration_direct_grouplist(self, configname):
        configuration = self.configuration(configname)
        if 'grouplist' in configuration.keys():
            return configuration['grouplist']
        else:
            return []

    def configuration_grouplist(self, configname):
        rval = ["default"]
        configuration = self.configuration(configname)
        if 'config' in configuration.keys():
            for section, sconfig in configuration['config'].iteritems():
                rval.extend(self.configsection_configgroups(section, sconfig))
        rval.extend(self._configuration_direct_grouplist(configname))
        while None in rval:
            rval.remove(None)
        return list(set(rval))

    def get_configuration(self, configname):
        warnings.warn("Deprecated access of get_configuration",
                      DeprecationWarning)
        return self.configuration_grouplist(configname)

    def configuration_motiflist(self, configname):
        # TODO Also deal with defaults here?
        configuration = self.configuration(configname)
        if 'motiflist' in configuration.keys():
            return configuration['motiflist']
        else:
            return None

    def get_configuration_motifs(self, configname):
        warnings.warn("Deprecated access of get_configuration_motifs",
                      DeprecationWarning)
        return self.configuration_motiflist(configname)

    def configuration_genlist(self, configname):
        configuration = self.configuration(configname)
        if 'genlist' in configuration.keys():
            return configuration['genlist']
        else:
            return None

    def get_configuration_gens(self, configname):
        warnings.warn("Deprecated access of get_configuration_gens",
                      DeprecationWarning)
        return self.configuration_genlist(configname)

    def configuration_sjlist(self, configname):
        if self.sjlist is not None:
            sjlist = copy.copy(self.sjlist)
        else:
            sjlist = None
        configuration = self.configuration(configname)
        if 'sjlist' in configuration.keys():
            csjlist = configuration['sjlist']
            if sjlist is not None:
                sjlist.update(csjlist)
                return sjlist
            else:
                return csjlist
        else:
            return sjlist

    def get_configuration_sjs(self, configname):
        warnings.warn("Deprecated access of get_configuration_sjs",
                      DeprecationWarning)
        return self.configuration_sjlist(configname)

    def description(self, configname=None):
        if configname is None:
            return self._configdata['desc']
        else:
            for configuration in self.configurations:
                if configuration['configname'] == configname:
                    return configuration['desc']
        raise ValueError

    def status_config(self, configname):
        raise NotImplementedError

    @property
    def status(self):
        raise NotImplementedError

    @property
    def snoseries(self):
        if 'snoseries' in self._configdata.keys():
            return self._configdata['snoseries']
        else:
            raise AttributeError('snoseries not defined or not found for {0}'
                                 ''.format(self._projectfolder))

    def testvars(self, configname):
        rval = {}
        for motif in self.motiflist:
            for k, v in self._configdata['motiflist'][motif].iteritems():
                rval[':'.join([motif, k])] = v
        for configuration in self._configdata['configurations']:
            if configuration['configname'] == configname:
                try:
                    rval.update(configuration['testvars'])
                except KeyError:
                    pass
                if "motiflist" in configuration.keys():
                    for motif in configuration['motiflist']:
                        for k, v in configuration['motiflist'][motif].iteritems():
                            rval[':'.join([motif, k])] = v
        return rval

    def tests(self):
        return self._configdata['tests']

    @property
    def rawconfig(self):
        return self._configdata

    @property
    def configdata(self):
        warnings.warn("Deprecated Access of configdata",
                      DeprecationWarning)
        return self._configdata

    @property
    def validation_errors(self):
        return self._validation_errors
