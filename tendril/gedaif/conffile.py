# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
gEDA ConfigsFile module documentation (:mod:`gedaif.conffile`)
==============================================================
"""


import logging
import os
import yaml


class NoGedaProjectException(Exception):
    pass


class ConfigsFile(object):
    def __init__(self, projectfolder):
        self._projectfolder = os.path.normpath(projectfolder)
        try:
            self.configdata = self.get_configs_file()
        except IOError:
            raise NoGedaProjectException(self._projectfolder)
        self.projectfile = self.configdata['projfile']

    def get_configs_file(self):
        with open(os.path.join(self.projectfolder, "schematic", "configs.yaml")) as configfile:  # noqa
            configdata = yaml.load(configfile)
        if configdata["schema"]["name"] == "pcbconfigs" and \
           configdata["schema"]["version"] == 1.0:
            return configdata
        else:
            logging.ERROR("Config file schema is not supported")

    @property
    def is_pcb(self):
        if 'pcbname' in self.configdata.keys() and \
                self.configdata['pcbname'] is not None:
            return True
        else:
            return False

    @property
    def is_cable(self):
        if 'cblname' in self.configdata.keys() and \
                self.configdata['cblname'] is not None:
            return True
        else:
            return False

    @property
    def doc_folder(self):
        return os.path.join(self.projectfolder, "doc")

    @property
    def indicative_pricing_folder(self):
        return os.path.join(self.doc_folder, "pricing")

    @property
    def projectfolder(self):
        return self._projectfolder

    @property
    def mactype(self):
        if 'mactype' in self.configdata:
            return self.configdata['mactype']
        else:
            raise AttributeError("No MACTYPE defined for this project")

    def description(self, configname=None):
        if configname is None:
            return self.configdata['desc']
        else:
            for configuration in self.configdata['configurations']:
                if configuration['configname'] == configname:
                    return configuration['desc']
        raise ValueError

    def testvars(self, configname):
        rval = {}
        for motif in self.configdata['motiflist']:
            for k, v in self.configdata['motiflist'][motif].iteritems():
                rval[':'.join([motif, k])] = v
        for configuration in self.configdata['configurations']:
            if configuration['configname'] == configname:
                try:
                    rval.update(configuration['testvars'])
                except KeyError:
                    pass
                for motif in configuration['motiflist']:
                    for k, v in configuration['motiflist'][motif].iteritems():
                        rval[':'.join([motif, k])] = v
        return rval

    @property
    def configurations(self):
        return [x for x in self.configdata['configurations']]

    def configuration(self, configname):
        for x in self.configdata['configurations']:
            if x['configname'] == configname:
                return x
        raise ValueError(configname + ' Not Found')

    @property
    def grouplist(self):
        return self.configdata["grouplist"]

    @property
    def motiflist(self):
        if "motiflist" in self.configdata.keys():
            return self.configdata["motiflist"]
        else:
            return []

    @property
    def sjlist(self):
        if "sjlist" in self.configdata.keys():
            return self.configdata["sjlist"]
        else:
            return {}

    @property
    def configsections(self):
        if "configsections" in self.configdata.keys():
            return self.configdata["configsections"]
        else:
            return None

    def get_configsections(self):
        if 'configsections' not in self.configdata.keys():
            return None
        rval = []
        for configsection in self.configdata['configsections']:
            rval.append(configsection["sectionname"])
        return rval

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

    def tests(self):
        return self.configdata['tests']

    @property
    def status(self):
        try:
            return self.configdata['pcbdetails']['status']
        except KeyError:
            raise KeyError(self._projectfolder)

    @property
    def pcbdescriptors(self):
        rval = [str(self.configdata['pcbdetails']['params']['dX']) + 'mm x ' +
                str(self.configdata['pcbdetails']['params']['dY']) + 'mm']
        if self.configdata['pcbdetails']["params"]["layers"] == 2:
            rval.append("Double Layer")
        elif self.configdata['pcbdetails']["params"]["layers"] == 4:
            rval.append("ML4")
        # HAL, Sn, Au, PBFREE, H, NP, I, OC
        if self.configdata['pcbdetails']["params"]["finish"] == 'Au':
            rval.append("Immersion Gold/ENIG finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'Sn':
            rval.append("Immersion Tin finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'PBFREE':
            rval.append("Any Lead Free finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'H':
            rval.append("Lead F ree HAL finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'NP':
            rval.append("No Copper finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'I':
            rval.append("OSP finish")
        elif self.configdata['pcbdetails']["params"]["finish"] == 'OC':
            rval.append("Only Copper finish")
        else:
            rval.append("UNKNOWN FINISH: " +
                        self.configdata['pcbdetails']["params"]["finish"])
        return rval
