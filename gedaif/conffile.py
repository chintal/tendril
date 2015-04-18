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
            raise NoGedaProjectException
        self.projectfile = self.configdata['projfile']
        if 'elprojfile' in self.configdata.keys():
            self.elprojfile = self.configdata['elprojfile']
        else:
            self.elprojfile = None

    def get_configs_file(self):
        with open(os.path.join(self.projectfolder, "schematic", "configs.yaml")) as configfile:
            configdata = yaml.load(configfile)
        if configdata["schema"]["name"] == "pcbconfigs" and \
           configdata["schema"]["version"] == 1.0:
            return configdata
        else:
            logging.ERROR("Config file schema is not supported")

    @property
    def projectfolder(self):
        return self._projectfolder
