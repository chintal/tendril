"""
gEDA ConfigsFile module documentation (:mod:`gedaif.conffile`)
==============================================================
"""


import logging
import os
import yaml


class ConfigsFile(object):
    def __init__(self, projectfolder):
        self.projectfolder = projectfolder
        self.configdata = self.get_configs_file(projectfolder)
        self.projectfile = self.configdata['projfile']

    @staticmethod
    def get_configs_file(projectfolder):
        with open(os.path.normpath(projectfolder+"/schematic/configs.yaml")) as configfile:
            configdata = yaml.load(configfile)
        if configdata["schema"]["name"] == "pcbconfigs" and \
           configdata["schema"]["version"] == 1.0:
            return configdata
        else:
            logging.ERROR("Config file schema is not supported")
