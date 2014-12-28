"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
import gedaif.bomparser

import os
import logging
import yaml


class EntityBase(object):

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

    """
    def __init__(self, item):
        super(EntityElnComp, self).__init__()
        self.refdes = item.data['refdes']
        self.device = item.data['device']
        self.value = item.data['value']
        if item.data['footprint'][0:3] == "MY-":
            self.footprint = item.data['footprint'][3:]
        else:
            self.footprint = item.data['footprint']
        self.fillstatus = item.data['fillstatus']
        self.ident = self.generate_ident()

    def generate_ident(self):
        ident = self.device + " " + self.value + " " + self.footprint
        return ident


class EntityGroup(EntityBase):
    """ Container for a group of entities

    Attributes:
        groupname
        eln_comp_list

    """

    def __init__(self, groupname):
        super(EntityGroup, self).__init__()
        self.groupname = groupname
        self.complist = []
        pass

    def insert(self, item):
        if item.data['fillstatus'] != 'DNP':
            x = EntityElnComp(item)
            self.complist.append(x)


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
        self.projfolder = cardfolder

        self.configurations = EntityBomConf(confdata)

        self.grouplist = []
        self.create_groups()

        self.populate_bom()

    def create_groups(self):
        x = EntityGroup('default')
        self.grouplist.append(x)
        for group in self.configurations.grouplist:
            x = EntityGroup(group)
            self.grouplist.append(x)

    def find_tgroup(self, item):
        """

        :rtype : EntityGroup
        """
        groupname = item.data['group']
        if groupname == 'unknown':
            groupname = 'default'
        if groupname not in self.configurations.grouplist:
            groupname = 'default'
            logging.warning("Could not find group in config file : " + groupname)
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def find_group(self, groupname):
        """

        :rtype : EntityGroup
        """
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def populate_bom(self):
        parser = gedaif.bomparser.GedaBomParser(self.projfolder, self.projfile, "bom")
        for item in parser.line_gen:
            tgroup = self.find_tgroup(item)
            tgroup.insert(item)

    def create_output_bom(self, configname):
        outbom = OutputBom(self.pcbname, self.projfolder, configname)
        outgroups = self.configurations.get_configuration(configname)
        for group in outgroups:
            grpobj = self.find_group(group)
            for comp in grpobj.complist:
                outbom.insert_component(comp)
        outbom.sort_by_ident()
        return outbom


class OutputBomLine(object):

    def __init__(self, comp):
        """

        :type comp: EntityElnComp
        """
        self.ident = comp.ident
        self.refdeslist = []

    def add(self, comp):
        """

        :type comp: EntityElnComp
        """
        if comp.ident == self.ident:
            self.refdeslist.append(comp.refdes)
        else:
            logging.error("Ident Mismatch")

    @property
    def quantity(self):
        return len(self.refdeslist)


class OutputBom(object):

    def __init__(self, pcbname, cardfolder, configname):
        self.pcbname = pcbname
        self.cardfolder = cardfolder
        self.configname = configname
        self.lines = []

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=True)

    def find_by_ident(self, ident):
        for line in self.lines:
            assert isinstance(line, OutputBomLine)
            if line.ident == ident:
                return line
        return None

    def insert_component(self, item):
        """

        :type item: EntityElnComp
        """
        line = self.find_by_ident(item.ident)
        if line is None:
            line = OutputBomLine(item)
            self.lines.append(line)
        line.add(item)


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
