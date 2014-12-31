"""
Electronic Boms Module documentation (:mod:`boms.electronics`)
==============================================================

This module contains various classes for handling structured data present in
elctronics BOMs. The module is built for use with gEDA with specific additions
and/or constraints to the standard gEDA project structure. Use with other EDA
tools should be possible by replacing ``gedaif`` with an EDA tool specific
package.

Module Summary:
---------------

.. autosummary::
    EntityBase
    EntityElnComp
    EntityGroup
    import_pcb

Module Members:
---------------

"""
import gedaif.bomparser
import gedaif.conffile

import logging


class EntityBase(object):
    """ Placeholder class for potentially track-able objects.

        Placeholder class for potentially track-able objects. Depending on the
        implementation used, this class should inherit from an external class
        built for this purpose instead of from ``object``.

    """
    def __init__(self):
        pass


class EntityElnComp(EntityBase):
    """Object containing a single electronic component.

        Accept a gedaif.bomparser.BomLine generated through gnetlist's
        ``bom`` backend. For a The ``attribs`` file should atleast contain:
        |  device
        |  value
        |  footprint
        |  fillstatus

        :param item: BomLine containing details of component to be created
        :type item: gedaif.bomparser.BomLine

    """
    def __init__(self, item=None):
        super(EntityElnComp, self).__init__()
        self._refdes = ""
        self._device = ""
        self._value = ""
        self._footprint = ""
        self._fillstatus = ""
        self._defined = False
        if item is not None:
            self.define(item.data['refdes'], item.data['device'],
                        item.data['value'], item.data['footprint'],
                        item.data['fillstatus'])

    def define(self, refdes, device, value, footprint="", fillstatus=""):
        self.refdes = refdes
        self.device = device
        self.value = value
        self.footprint = footprint
        self.fillstatus = fillstatus
        self._defined = True

    @property
    def defined(self):
        return self._defined

    @property
    def refdes(self):
        """ Refdes string. """
        return self._refdes

    @refdes.setter
    def refdes(self, value):
        self._refdes = value

    @property
    def fillstatus(self):
        """ Fillstatus string. """
        return self._fillstatus

    @fillstatus.setter
    def fillstatus(self, value):
        if value == 'DNP':
            self._fillstatus = 'DNP'
        elif value in ['unknown', '']:
            self._fillstatus = ''
        else:
            logging.warning("Unsupported fillstatus: " + value)

    @property
    def ident(self):
        """
        Auto-generated ident string from the component ``device``, ``value``
        and ``footprint`` attributes. This is a read-only property.
        """
        ident = self.device + " " + self.value + " " + self.footprint
        return ident.strip()

    @property
    def device(self):
        """ Component device string. """
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def value(self):
        """ Component value string. """
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def footprint(self):
        """
        Component footprint string. ``MY-`` at the beginning of the footprint
        string is stripped away automatically.
        """
        return self._footprint

    @footprint.setter
    def footprint(self, value):
        if value[0:3] == "MY-":
            self._footprint = value[3:]
        else:
            self._footprint = value


class EntityGroup(EntityBase):
    """ Container for a group of EntityElnComp objects.

        :ivar groupname: Name of the group
        :ivar eln_comp_list: List of EntityElnComp objects

    """
    def __init__(self, groupname):
        super(EntityGroup, self).__init__()
        self.groupname = groupname
        self.complist = []
        pass

    def insert(self, item):
        """ Insert an electronic component into the EntityGroup.

        Accept a BomLine and generate an EntityElnComp to represent the
        component if it's fillstatus is not ``DNP``. Insert the created
        EntityElnComp object into the group.

        :type item: gedaif.bomparser.BomLine

        """
        if item.data['fillstatus'] != 'DNP':
            x = EntityElnComp(item)
            if x.defined:
                self.complist.append(x)

    def insert_comp(self, comp):
        """

        :type comp: EntityElnComp
        """
        if comp.defined:
            self.complist.append(comp)


class EntityBomConf(object):
    def __init__(self, configdata):
        super(EntityBomConf, self).__init__()
        self.pcbname = configdata["pcbname"]
        self.grouplist = configdata["grouplist"]
        self.configsections = configdata["configsections"]
        self.configurations = configdata["configurations"]

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
    def __init__(self, configfile):

        """

        :type configfile: gedaif.conffile.ConfigsFile
        """
        super(EntityBom, self).__init__()
        self.pcbname = configfile.configdata["pcbname"]
        self.projfile = configfile.configdata["projfile"]
        self.projfolder = configfile.projectfolder

        self.configurations = EntityBomConf(configfile.configdata)

        self.grouplist = []
        self.create_groups()

        self.populate_bom()

    def create_groups(self):
        x = EntityGroup('default')
        self.grouplist.append(x)
        groupnamelist = [x['name'] for x in self.configurations.grouplist]
        for group in groupnamelist:
            logging.debug("Creating Group: " + str(group))
            x = EntityGroup(group)
            self.grouplist.append(x)

    def find_tgroup(self, item):
        """

        :rtype : EntityGroup
        """
        groupname = item.data['group']
        if groupname == 'unknown':
            groupname = 'default'
        if groupname not in [x['name'] for x in self.configurations.grouplist]:
            logging.warning("Could not find group in config file : " + groupname)
            groupname = 'default'
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
        tgroup = self.find_group('default')
        comp = EntityElnComp()
        comp.define('PCB', 'PCB', self.configurations.pcbname)
        tgroup.insert_comp(comp)
        parser = gedaif.bomparser.GedaBomParser(self.projfolder, "bom")
        for item in parser.line_gen:
            tgroup = self.find_tgroup(item)
            tgroup.insert(item)

    def create_output_bom(self, configname):
        outbomdescriptor = OutputBomDescriptor(self.pcbname, self.projfolder, configname, self.configurations)
        outbom = OutputBom(outbomdescriptor)
        outgroups = self.configurations.get_configuration(configname)
        for group in outgroups:
            grpobj = self.find_group(group)
            for comp in grpobj.complist:
                outbom.insert_component(comp)
        outbom.sort_by_ident()
        return outbom


class OutputBomDescriptor(object):
    def __init__(self, pcbname, cardfolder, configname, configurations, multiplier=1):
        self.pcbname = pcbname
        self.cardfolder = cardfolder
        self.configname = configname
        self.multiplier = multiplier
        self.configurations = configurations


class OutputBomLine(object):

    def __init__(self, comp, parent):
        """


        :type parent: OutputBom
        :type comp: EntityElnComp
        """
        self.ident = comp.ident
        self.refdeslist = []
        self.parent = parent

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
        return len(self.refdeslist) * self.parent.descriptor.multiplier


class OutputBom(object):

    def __init__(self, descriptor):
        """

        :type descriptor: OutputBomDescriptor
        """
        self.lines = []
        self.descriptor = descriptor

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)

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
            line = OutputBomLine(item, self)
            self.lines.append(line)
        line.add(item)

    def multiply(self, factor, composite=False):
        if composite is True:
            self.descriptor.multiplier = self.descriptor.multiplier * factor
        else:
            self.descriptor.multiplier = factor


class CompositeOutputBomLine(object):

    def __init__(self, line, colcount):
        self.ident = line.ident
        self.columns = [0] * colcount

    def add(self, line, column):
        """

        :type line: OutputBomLine
        """
        if line.ident == self.ident:
            self.columns[column] = line.quantity
        else:
            logging.error("Ident Mismatch")

    @property
    def quantity(self):
        return sum(self.columns)


class CompositeOutputBom():
    def __init__(self, bom_list):
        self.descriptors = []
        self.lines = []
        self.colcount = len(bom_list)
        i = 0
        for bom in bom_list:
            self.insert_bom(bom, i)
            i += 1
        self.sort_by_ident()

    def insert_bom(self, bom, i):
        """

        :type bom: OutputBom
        """
        self.descriptors.append(bom.descriptor)
        for line in bom.lines:
            self.insert_line(line, i)

    def insert_line(self, line, i):
        """

        :type line: OutputBomLine
        """
        cline = self.find_by_ident(line)
        if cline is None:
            cline = CompositeOutputBomLine(line, self.colcount)
            self.lines.append(cline)
        cline.add(line, i)

    def find_by_ident(self, line):
        """

        :type line: OutputBomLine
        """
        for cline in self.lines:
            assert isinstance(cline, CompositeOutputBomLine)
            if cline.ident == line.ident:
                return cline
        return None

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)


def import_pcb(cardfolder):
    """Import PCB and return a populated EntityBom

    Accept cardfolder as an argument and return a populated EntityBOM.
    The cardfolder should be the path to a PCB folder, containing the
    file structure described in ``somewhere``.

    .. seealso:: ``gedaif.projfile.GedaProjectFile``
    .. seealso:: ``gEDA Project Folder Structure``

    :param cardfolder: PCB folder (containing schematic, pcb, gerber)
    :type cardfolder: str
    :return: Populated EntityBom
    :rtype: EntityBom

    :Example:

    >>> import boms.electronics
    >>> bom = boms.electronics.import_pcb('path/to/cardfolder')

    """
    pcbbom = None
    configfile = gedaif.conffile.ConfigsFile(cardfolder)
    if configfile.configdata is not None:
        pcbbom = EntityBom(configfile)
    return pcbbom

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    data = import_pcb("/home/chintal/code/koala/scratch")
