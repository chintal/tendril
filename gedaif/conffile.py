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

    def get_configs_file(self):
        with open(os.path.join(self.projectfolder, "schematic", "configs.yaml")) as configfile:
            configdata = yaml.load(configfile)
        if configdata["schema"]["name"] == "pcbconfigs" and \
           configdata["schema"]["version"] == 1.0:
            return configdata
        else:
            logging.ERROR("Config file schema is not supported")

    @property
    def doc_folder(self):
        return os.path.join(self.projectfolder, "doc")

    @property
    def indicative_pricing_folder(self):
        return os.path.join(self.doc_folder, "pricing")

    @property
    def projectfolder(self):
        return self._projectfolder

    def description(self, configname=None):
        if configname is None:
            return self.configdata['desc']
        else:
            for configuration in self.configdata['configurations']:
                if configuration['configname'] == configname:
                    return configuration['desc']
        raise ValueError
