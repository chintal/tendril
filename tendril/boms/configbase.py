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
import yaml
import itertools
import warnings

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class NoProjectError(Exception):
    pass


class SchemaNotSupportedError(Exception):
    pass


class ConfigBase(object):
    NoProjectErrorType = NoProjectError

    def __init__(self, projectfolder):
        self._projectfolder = os.path.normpath(projectfolder)
        try:
            self._configdata = self.get_configs_file()
        except IOError:
            raise self.NoProjectErrorType(self._projectfolder)

    @property
    def _cfpath(self):
        raise NotImplementedError

    def get_configs_file(self):
        with open(self._cfpath) as configfile:
            configdata = yaml.load(configfile)
            try:
                return self._verify_schema_decl(configdata)
            except SchemaNotSupportedError:
                logger.error("Schema not supported for project : {0}"
                             "".format(self._projectfolder))

    def _verify_schema_decl(self, configdata):
        raise NotImplementedError

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
    def sjlist(self):
        if "sjlist" in self._configdata.keys():
            return self._configdata["sjlist"]
        else:
            return {}

    @property
    def genlist(self):
        raise NotImplementedError

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
                    nconfig['configname'] = nconfig['configname'].replace(
                            '<{0}:{1}>'.format(dimname, 'tpart'),
                            component['tpart']
                    )
                    # Update all others
                    for param, action in lactions.iteritems():
                        if action == 'pass':
                            continue
                        if action == 'update':
                            if param in ['genlist']:
                                nconfig[param].update(component[param])
                                continue
                        raise AttributeError("{0} Action not recognized for "
                                             "{1} {2}".format(
                                                action, param,
                                                self._projectfolder))
                rval.append(nconfig)
        return rval

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
                rval.append(configurations)
        return rval

    @property
    def configuration_names(self):
        return [x['configname'] for x in self.configurations]

    def configuration(self, configname):
        for x in self._configdata['configurations']:
            if x['configname'] == configname:
                return x
        raise ValueError(configname + ' Not Found')

    @property
    def configsections(self):
        if "configsections" in self._configdata.keys():
            return self._configdata["configsections"]
        else:
            return []

    @property
    def configsection_names(self):
        return [x['sectionname'] for x in self.configsections]

    def get_sec_groups(self, sectionname, configname):
        rval = []
        for section in self.configsections:
            if section["sectionname"] == sectionname:
                for configuration in section["configurations"]:
                    if configuration["configname"] == configname:
                        for group in configuration["groups"]:
                            if group is not None:
                                rval.append(group)
        return rval

    def config_grouplist(self, configname):
        rval = ["default"]
        for configuration in self.configurations:
            if configuration["configname"] == configname:
                try:
                    for configsection in self.get_configsections():
                        sec_confname = configuration["config"][configsection]
                        rval = rval + self.get_sec_groups(configsection,
                                                          sec_confname)
                except TypeError:
                    rval = ["default"]
                    try:
                        for group in configuration["grouplist"]:
                            if group != "default":
                                rval = rval + [group]
                    except:
                        raise AttributeError
        return rval

    def description(self, configname=None):
        if configname is None:
            return self._configdata['desc']
        else:
            for configuration in self._configdata['configurations']:
                if configuration['configname'] == configname:
                    return configuration['desc']
        raise ValueError

    def status_config(self, configname):
        raise NotImplementedError

    @property
    def status(self):
        if 'status' in self._configdata.keys():
            return self._configdata['status']
        else:
            raise AttributeError('Status not defined or not found for {0}'
                                 ''.format(self._projectfolder))

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
