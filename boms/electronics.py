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
import conventions.electronics

from outputbase import OutputElnBomDescriptor
from outputbase import OutputBom
from entitybase import EntityBase
from entitybase import EntityGroupBase
from entitybase import EntityBomBase

import os
import logging


class EntityElnComp(EntityBase):
    """Object containing a single electronic component.

        Accept a ``gedaif.bomparser.BomLine`` generated through gnetlist's
        ``bom`` backend. The ``attribs`` file should atleast contain:
         * device
         * value
         * footprint
         * fillstatus

        :param item: BomLine containing details of component to be created
        :type item: gedaif.bomparser.BomLine

    """
    def __init__(self, item=None):
        super(EntityElnComp, self).__init__()
        self._device = ""
        self._value = ""
        self._footprint = ""
        self._fillstatus = ""

        if item is not None:
            self.define(item.data['refdes'], item.data['device'],
                        item.data['value'], item.data['footprint'],
                        item.data['fillstatus'])

    def define(self, refdes, device, value, footprint="", fillstatus=""):
        """
        Define the component.

        Can be used directly for special cases when there is no
        `gedaif.bomparser.BomLine` to pass to the class `__init__`
        function.

        :param refdes: Refdes string.
        :param device: Device string.
        :param value: Value string.
        :param footprint: Footprint string. Optional.
        :param fillstatus: Fillstatus string. Optional.
        """
        self.refdes = refdes
        self.device = device
        self.value = value
        self.footprint = footprint
        self.fillstatus = fillstatus
        self._defined = True

    @property
    def fillstatus(self):
        """ Fillstatus string.
        When ``fillstatus`` is ``DNP``, the component is not included in BOMs
        irrespective of other configuration states.
        """
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
        return conventions.electronics.ident_transform(self.device,
                                                       self.value,
                                                       self.footprint)

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


class EntityElnGroup(EntityGroupBase):
    """ Container for a group of EntityElnComp objects.

        :ivar groupname: Name of the group
        :ivar eln_comp_list: List of EntityElnComp objects

    """
    def __init__(self, groupname, contextname):
        super(EntityElnGroup, self).__init__(groupname, contextname)
        pass

    def insert(self, item):
        """ Insert an electronic component into the EntityGroup.

        Accept a BomLine and generate an EntityElnComp to represent the
        component if it's ``fillstatus`` is not ``DNP``. Insert the created
        EntityElnComp object into the group.

        :param item: ``BomLine`` representing the item to insert.
        :type item: gedaif.bomparser.BomLine

        """
        if item.data['fillstatus'] != 'DNP':
            x = EntityElnComp(item)
            if x.defined:
                self.complist.append(x)

    def insert_eln_comp(self, comp):
        """ Insert a manually created component into the EntityGroup.

        This should be used for components not originating directly from
        gEDA's gnetlist output.

        :param comp: Existing component to insert
        :type comp: EntityElnComp
        """
        if comp.defined:
            self.complist.append(comp)


class EntityElnBomConf(object):
    def __init__(self, configdata):
        super(EntityElnBomConf, self).__init__()
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


class EntityElnBom(EntityBomBase):
    def __init__(self, configfile):

        """

        :type configfile: gedaif.conffile.ConfigsFile
        """
        super(EntityElnBom, self).__init__()
        self.pcbname = configfile.configdata["pcbname"]
        self.projfile = configfile.configdata["projfile"]
        self.projfolder = configfile.projectfolder

        self.configurations = EntityElnBomConf(configfile.configdata)

        self.create_groups()
        self.populate_bom()

    def create_groups(self):
        groupnamelist = [x['name'] for x in self.configurations.grouplist]
        if 'default' not in groupnamelist:
            x = EntityElnGroup('default', self.pcbname)
            self.grouplist.append(x)
        for group in groupnamelist:
            logging.debug("Creating Group: " + str(group))
            x = EntityElnGroup(group, self.pcbname)
            self.grouplist.append(x)

    def find_tgroup(self, item):
        """

        :rtype : EntityElnGroup
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

        :rtype : EntityElnGroup
        """
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def populate_bom(self):
        tgroup = self.find_group('default')
        comp = EntityElnComp()
        comp.define('PCB', 'PCB', self.configurations.pcbname)
        tgroup.insert_eln_comp(comp)
        parser = gedaif.bomparser.GedaBomParser(self.projfolder, "bom")
        for item in parser.line_gen:
            tgroup = self.find_tgroup(item)
            tgroup.insert(item)

    def create_output_bom(self, configname):
        outbomdescriptor = OutputElnBomDescriptor(self.pcbname, self.projfolder, configname, self.configurations)
        outbom = OutputBom(outbomdescriptor)
        outgroups = self.configurations.get_configuration(configname)
        for group in outgroups:
            grpobj = self.find_group(group)
            for comp in grpobj.complist:
                outbom.insert_component(comp)
        outbom.sort_by_ident()
        return outbom


def import_pcb(cardfolder):
    """Import PCB and return a populated EntityBom

    Accept cardfolder as an argument and return a populated EntityBOM.
    The cardfolder should be the path to a PCB folder, containing the
    file structure described in ``somewhere``.

    .. seealso::
        - ``gedaif.projfile.GedaProjectFile``
        - ``gEDA Project Folder Structure``

    :param cardfolder: PCB folder (containing schematic, pcb, gerber)
    :type cardfolder: str
    :return: Populated EntityBom
    :rtype: EntityBom

    :Example:

    >>> import boms.electronics
    >>> bom = boms.electronics.import_pcb('path/to/cardfolder')

    """
    cardfolder = os.path.abspath(cardfolder)
    pcbbom = None
    configfile = gedaif.conffile.ConfigsFile(cardfolder)
    if configfile.configdata is not None:
        pcbbom = EntityElnBom(configfile)
    return pcbbom

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    data = import_pcb("/home/chintal/code/koala/scratch")
