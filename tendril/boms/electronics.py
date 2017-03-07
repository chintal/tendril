#!/usr/bin/env python
# encoding: utf-8

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
    EntityElnGroup
    import_pcb

Module Members:
---------------

"""

import copy
import os
import warnings

from tendril.conventions.electronics import fpiswire
from tendril.conventions.electronics import ident_transform
from tendril.gedaif.bomparser import MotifAwareBomParser
from tendril.gedaif.conffile import ConfigsFile

from tendril.entityhub.entitybase import EntityBase
from tendril.entityhub.entitybase import EntityBomBase
from tendril.entityhub.entitybase import EntityGroupBase

from .validate import ValidationContext
from .validate import ErrorCollector
from .validate import ValidationError
from .validate import BomGroupPolicy
from .validate import ConfigMotifPolicy
from .validate import ConfigMotifMissingError
from .validate import ConfigGroupError
from .validate import ConfigGroupPolicy
from .validate import ConfigSJPolicy
from .validate import ConfigSJUnexpectedError

from .outputbase import OutputBom
from .outputbase import OutputElnBomDescriptor
from .costingbase import HierachicalCostingBreakup
from .costingbase import NoStructureHereException

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


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
                        item.data['fillstatus'], item.data['schfile'])

    def define(self, refdes, device, value, footprint="", fillstatus="",
               schfile=None):
        """
        Define the component.

        Can be used directly for special cases when there is no
        `tendril.gedaif.bomparser.BomLine` to pass to the class `__init__`
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
        self.schfile = None

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
        elif value == 'CONF':
            self._fillstatus = 'CONF'
        else:
            logger.warning("Unsupported fillstatus: " + value)

    @property
    def ident(self):
        return ident_transform(self.device, self.value, self.footprint)

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
        if value is None:
            return
        if value[0:3] == "MY-":
            self._footprint = value[3:]
        else:
            self._footprint = value


class EntityElnGroup(EntityGroupBase):
    """ Container for a group of EntityElnComp objects.

        :ivar groupname: Name of the group

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


class EntityElnBomConf(ConfigsFile):
    pass


class EntityElnBom(EntityBomBase):
    def __init__(self, configfile, use_cached=True):
        """

        :type configfile: gedaif.conffile.ConfigsFile
        """
        super(EntityElnBom, self).__init__()
        self.configurations = configfile
        self._included_motifs = []
        self._motifs = []
        self._configured_for = None
        self._validation_context = ValidationContext(
                    self.configurations.projectfolder, 'BOM')
        self._group_policy = None
        self._validation_errors = ErrorCollector()
        self.create_groups()
        self.populate_bom(use_cached=use_cached)

    @property
    def validation_errors(self):
        return self._validation_errors

    @property
    def pcbname(self):
        warnings.warn("Deprecated access of pcbname",
                      DeprecationWarning)
        return self.configurations.pcbname

    @property
    def projfile(self):
        warnings.warn("Deprecated access of projfile",
                      DeprecationWarning)
        return self.configurations.projectfile

    @property
    def projectfolder(self):
        warnings.warn("Deprecated access of projectfolder",
                      DeprecationWarning)
        return self.configurations.projectfolder

    @property
    def motifs(self, all_defined=False):
        if all_defined:
            return sorted(self._motifs,
                          key=lambda x: (x._type, int(x._ident)))
        else:
            return sorted(self._included_motifs,
                          key=lambda x: (x._type, int(x._ident)))

    def create_groups(self):
        groupnamelist = self.configurations.group_names
        file_groups = self.configurations.file_groups
        if 'default' not in groupnamelist:
            groupnamelist.append('default')
        for group in groupnamelist:
            logger.debug("Creating Group: " + str(group))
            x = EntityElnGroup(group, self.configurations.pcbname)
            self.grouplist.append(x)
        self._group_policy = BomGroupPolicy(self._validation_context,
                                            groupnamelist, file_groups)

    def find_group(self, groupname):
        """

        :rtype : EntityElnGroup
        """
        for group in self.grouplist:
            if group.groupname == groupname:
                return group

    def find_tgroup(self, item):
        """

        :rtype : EntityElnGroup
        """
        try:
            gname = self._group_policy.check(item)
        except ValidationError as e:
            self._validation_errors.add(e)
            gname = self._group_policy.default
        return self.find_group(gname)

    def _add_item(self, item):
        # TODO This function includes very specific special cases
        # These need to come out of core and into the instance.
        if item.data['device'] in {'TESTPOINT', 'PCB EDGE'}:
            return
        tgroup = self.find_tgroup(item)
        skip = False
        if item.data['footprint'] == 'MY-TO220':
            comp = EntityElnComp()
            comp.define('HS' + item.data['refdes'][1:],
                        'HEAT SINK', 'TO220')
            tgroup.insert_eln_comp(comp)
        if item.data['device'] == 'MODULE LCD' and \
                item.data['value'] == "CHARACTER PARALLEL 16x2" and \
                item.data['footprint'] == "MY-MTA100-16":
            comp = EntityElnComp()
            comp.define(
                item.data['refdes'], 'CONN SIP',
                "16PIN PM ST", "MY-MTA100-16"
            )
            tgroup.insert_eln_comp(comp)
            skip = True
        if item.data['device'] == 'RES SMD' and \
                item.data['value'] == '0E':
            comp = EntityElnComp()
            comp.define(
                item.data['refdes'], 'SOLDER DOT', '0E',
                footprint='MY-0603', fillstatus=item.data['fillstatus']
            )
            tgroup.insert_eln_comp(comp)
            skip = True
        if item.data['value'].startswith('DUAL'):
            fp = item.data['footprint']
            # if fp.endswith('-2'):
            #     fp = fp[:-1 * len('-2')]
            comp = EntityElnComp()
            comp.define(
                refdes=item.data['refdes'] + '.1',
                device=item.data['device'],
                value=item.data['value'].split(' ', 1)[1],
                footprint=fp,
                fillstatus=item.data['fillstatus']
            )
            tgroup.insert_eln_comp(comp)
            comp = EntityElnComp()
            comp.define(
                refdes=item.data['refdes'] + '.2',
                device=item.data['device'],
                value=item.data['value'].split(' ', 1)[1],
                footprint=fp,
                fillstatus=item.data['fillstatus']
            )
            tgroup.insert_eln_comp(comp)
            skip = True
        if not skip:
            tgroup.insert(item)

    def populate_bom(self, use_cached=True):
        if self.configurations.pcbname is not None:
            tgroup = self.find_group('default')
            comp = EntityElnComp()
            comp.define('PCB', 'PCB', self.configurations.pcbname)
            tgroup.insert_eln_comp(comp)
        parser = MotifAwareBomParser(self.configurations.projectfolder,
                                     use_cached=use_cached, backend="bom")
        for item in parser.line_gen:
            self._add_item(item)
        for motif in parser.motif_gen:
            self._motifs.append(motif)
        self._validation_errors.add(parser.validation_errors)

    def get_motif_by_refdes(self, refdes):
        for motif in self._motifs:
            if refdes == motif.refdes:
                return motif
        return None

    @property
    def configured_for(self):
        return self._configured_for

    def configure_motifs(self, configname):
        self._configured_for = configname
        self._included_motifs = []
        ctx = copy.copy(self._validation_context)
        ctx.locality = 'BOM_CM_{0}'.format(configname)
        motifconfs = self.configurations.configuration_motiflist(configname)
        if motifconfs is not None:
            policy = ConfigMotifPolicy(ctx)
            for key, motifconf in motifconfs.iteritems():
                motif = self.get_motif_by_refdes(key)
                if motif is None:
                    e = ConfigMotifMissingError(policy, key)
                    self._validation_errors.add(e)
                    continue
                motif_actconf = motif.get_configdict_stub()
                if self.configurations.motiflist is not None:
                    motif_actconf.update(self.configurations.motif_baseconf(key))
                motif_actconf.update(motifconf)
                motif.configure(motif_actconf)
                self._included_motifs.append(motif)

    def create_output_bom(self, configname, groupname=None):
        if configname not in self.configurations.configuration_names:
            raise ValueError
        outbomdescriptor = OutputElnBomDescriptor(
            self.configurations.pcbname,
            self.configurations.projectfolder,
            configname, self.configurations,
            groupname=groupname
        )
        outbom = OutputBom(outbomdescriptor)
        if groupname is None:
            is_group_bom = False
            outgroups = self.configurations.configuration_grouplist(configname)  # noqa
        else:
            is_group_bom = True
            outgroups = [groupname]

        genlist = self.configurations.configuration_genlist(configname)
        gen_refdeslist = None
        if genlist is not None:
            gen_refdeslist = genlist.keys()

        sjlist = self.configurations.configuration_sjlist(configname)
        sj_refdeslist = None
        if sjlist is not None:
            sj_refdeslist = sjlist.keys()

        ctx = self._validation_context
        _policy_ge = ConfigGroupPolicy(ctx, self._group_policy.known_groups)
        _policy_sj = ConfigSJPolicy(ctx)

        for group in outgroups:
            grpobj = self.find_group(group)
            if grpobj is None:
                e = ConfigGroupError(_policy_ge, group)
                self._validation_errors.add(e)
                continue
            for comp in grpobj.complist:
                if gen_refdeslist is not None and \
                        comp.refdes in gen_refdeslist:
                    # TODO Verify refdes has Generator status in schematic
                    if fpiswire(comp.device):
                        comp.footprint = genlist[comp.refdes]
                    else:
                        comp.value = genlist[comp.refdes]
                if sj_refdeslist is not None and comp.refdes in sj_refdeslist:
                    if not comp.fillstatus == 'CONF':
                        e = ConfigSJUnexpectedError(_policy_sj,
                                                    comp.refdes,
                                                    comp.fillstatus)
                        self._validation_errors.add(e)
                    if sjlist[comp.refdes]:
                        logger.debug("Setting Fillstatus : " + comp.refdes)
                        comp.fillstatus = ''
                    else:
                        logger.debug("Clearing Fillstatus : " + comp.refdes)
                        comp.fillstatus = 'DNP'
                outbom.insert_component(comp)

        motifconfs = self.configurations.configuration_motiflist(configname)
        if motifconfs is None:
            outbom.sort_by_ident()
            outbom.validation_errors.add(self._validation_errors)
            return outbom

        if self._configured_for != configname:
            self.configure_motifs(configname)

        for key, motifconf in motifconfs.iteritems():
            motif = self.get_motif_by_refdes(key)
            if motif is None:
                # This error would already have beed reported when
                # motifs were configured.
                logger.error("Motif not defined : " + key)
                continue
            for item in motif.get_line_gen():
                item_group = item.data['group']
                if item_group == 'unknown' or item_group in outgroups and \
                        item.data['fillstatus'] != 'DNP':
                    outbom.insert_component(EntityElnComp(item))

        outbom.sort_by_ident()
        outbom.validation_errors.add(self._validation_errors)
        return outbom

    def get_group_boms(self, configname):
        if configname not in self.configurations.configuration_names:
            raise ValueError
        rval = []
        for group in self.configurations.configuration_grouplist(configname):
            rval.append(self.create_output_bom(configname, groupname=group))
        return rval

    def indicative_cost_hierarchical_breakup(self, configname):
        group_boms = self.get_group_boms(configname)
        if len(group_boms) == 1:
            raise NoStructureHereException
        rval = HierachicalCostingBreakup(configname)
        for obom in group_boms:
            rval.insert(obom.descriptor.groupname,
                        obom.indicative_cost_breakup)
        return rval


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

    >>> import tendril.boms.electronics
    >>> bom = tendril.boms.electronics.import_pcb('path/to/cardfolder')

    """
    cardfolder = os.path.abspath(cardfolder)
    pcbbom = None
    configfile = ConfigsFile(cardfolder)
    if configfile.rawconfig is not None:
        pcbbom = EntityElnBom(configfile)
    return pcbbom


if __name__ == "__main__":
    pass
