"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
import os
import logging
import yaml


class EntityBase(object):
    id = None

    def __init__(self):
        pass


class EntityElnComp(EntityBase):
    """ Container for a single Electronic component

    Attributes:
        refdes
        device
        value
        footprint
        inventory_link
        parent_group

    """
    def __init__(self):
        super(EntityElnComp, self).__init__()

        pass


class EntityGroup(EntityBase):
    """ Container for a group of entities

    Attributes:
        groupname
        eln_comp_list
        parent_bom

    """
    def __init__(self):
        super(EntityGroup, self).__init__()
        pass


class EntityBomConf(EntityBase):
    """All allowed configurations for a PCB

    Attributes:
        grouplist
        configsections(L)
            configsection
            grouplist
            configurations(L)
                configname
                groups
        configurations(L)
            configname
            config

    """
    def __init__(self, confdata):
        super(EntityBomConf, self).__init__()
        self.grouplist = confdata["grouplist"]
        self.configsections = confdata["configsections"]
        self.configurations = confdata["configurations"]

    def get_configurations(self):
        rval = []
        for configuration in self.configurations:
            rval.append(configuration["configname"])
        return rval
        pass

    def get_configsections(self):
        rval = []
        for configsection in self.configsections:
            rval.append(configsection["sectionname"])
        return rval

    def get_sec_groups(self, sectionname, config):
        rval = []
        for section in self.configsections:
            if section["sectionname"] == sectionname:
                for configuration in section["configurations"]:
                    if configuration["configname"] == config:
                        for group in configuration["groups"]:
                            rval.append(group)
        return rval

    def get_configuration(self, configname):
        rval = ["default"]
        for configuration in self.configurations:
            if configuration["configname"] == configname:
                for configsection in self.get_configsections():
                    sec_confname = configuration["config"][configsection]
                    rval = rval + self.get_sec_groups(configsection, sec_confname)
        return rval


class EntityBom(EntityBase):
    """Single Bill of Materials Container

    An EntityBom is a collection of EntityGroups,

    Attributes:
        configurations
        grouplist

    """
    def __init__(self, confdata, cardfolder):
        super(EntityBom, self).__init__()
        self.pcbname = confdata["pcbname"]
        self.projfile = confdata["projfile"]
        self.pcbfolder = cardfolder
        self.configurations = EntityBomConf(confdata)
        pass


def import_pcb(cardfolder):
    pcbbom = None
    with open(os.path.normpath(cardfolder+"/schematic/configs.yaml")) as configfile:
        configdata = yaml.load(configfile)
    if configdata["schema"]["name"] == "pcbconfigs" and \
       configdata["schema"]["version"] == 1.0:
        pcbbom = EntityBom(configdata, cardfolder)
    else:
        logging.ERROR("Config file schema is not supported")
    return pcbbom

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    data = import_pcb("/home/chintal/code/koala/scratch")
