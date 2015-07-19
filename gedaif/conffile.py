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

    @property
    def configurations(self):
        return [x['configname'] for x in self.configdata['configurations']]

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
            rval.append("UNKNOWN FINISH: " + self.configdata['pcbdetails']["params"]["finish"])
        return rval
