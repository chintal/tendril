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
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import csv
from decimal import Decimal

from tendril.conventions.electronics import fpiswire
from tendril.conventions.electronics import parse_ident
from tendril.entityhub.entitybase import EntityBase
from tendril.entityhub.entitybase import GenericEntityBase
from tendril.utils import log
from tendril.utils.types.lengths import Length
from tendril.utils.types.unitbase import NumericalUnitBase

from .costingbase import SourcingIdentPolicy
from .costingbase import SourceableBomLineMixin
from .costingbase import CostableBom

from .validate import ErrorCollector
from .validate import ValidationContext

logger = log.get_logger(__name__, log.DEFAULT)


class OutputElnBomDescriptor(object):
    def __init__(self, pcbname, cardfolder, configname,
                 configurations, multiplier=1, groupname=None):
        self.pcbname = pcbname
        self.cardfolder = cardfolder
        self.configname = configname
        self.multiplier = multiplier
        self.configurations = configurations
        # For group boms
        self.groupname = groupname


class OutputBomLine(SourceableBomLineMixin):
    def __init__(self, comp, parent):
        super(OutputBomLine, self).__init__()
        assert isinstance(comp, EntityBase)
        self._ident = comp.ident
        self._refdeslist = []
        self._parent = parent

    @property
    def ident(self):
        return self._ident

    @ident.setter
    def ident(self, value):
        self._ident = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def refdeslist(self):
        return self._refdeslist

    @refdeslist.setter
    def refdeslist(self, value):
        self._refdeslist = value

    def add(self, comp):
        assert isinstance(comp, EntityBase)
        if hasattr(comp, 'fillstatus'):
            if comp.fillstatus == "DNP":
                return
            if comp.fillstatus == "CONF":
                # TODO
                # logger.warning("Configurable Component "
                #                "not Configured by Conf File : " + comp.refdes)
                pass
        if comp.ident == self.ident:
            self.refdeslist.append(comp.refdes)
        else:
            logger.error("Ident Mismatch")
            raise Exception

    @property
    def uquantity(self):
        device, value, footprint = parse_ident(self.ident)
        if device is None:
            # TODO
            # logger.warning("Device not identified : " + self.ident)
            pass
        elif fpiswire(device):
            try:
                elen = Length(footprint) * Decimal(0.1)
                if elen < Length('5mm'):
                    elen = Length('5mm')
                elif elen > Length('1inch'):
                    elen = Length('1inch')
                return len(self.refdeslist) * (Length(footprint) + elen)
            except ValueError:
                logger.error(
                    "Problem parsing length for ident : " + self.ident
                )
                raise
        return len(self.refdeslist)

    @property
    def quantity(self):
        qty = self.uquantity * self.parent.descriptor.multiplier
        return qty

    @property
    def quantity_str(self):
        qty = self.quantity
        if isinstance(qty, NumericalUnitBase):
            qty = qty.integral_repr
        else:
            qty = str(qty)
        return qty

    def __repr__(self):
        return "{0:<50} {1:<4} {2}".format(
            self.ident, self.quantity, str(self.refdeslist)
        )


class OutputBom(CostableBom):
    def __init__(self, descriptor):
        """

        :type descriptor: outputbase.OutputElnBomDescriptor
        """
        super(OutputBom, self).__init__()
        self.descriptor = descriptor
        if self.descriptor.groupname is not None:
            locality = 'OBOM.{0}'.format(self.descriptor.groupname)
        else:
            locality = 'OBOM'
        self._validation_context = ValidationContext(
            self.descriptor.configname, locality
        )
        self.sourcing_policy = SourcingIdentPolicy(self._validation_context)
        self.validation_errors = ErrorCollector()

    @property
    def ident(self):
        if self.descriptor.groupname is not None:
            return '.'.join([self.descriptor.configname,
                             self.descriptor.groupname])
        else:
            return self.descriptor.configname

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)
        for line in self.lines:
            line.refdeslist.sort()

    def find_by_ident(self, ident):
        for line in self.lines:
            assert isinstance(line, OutputBomLine)
            if line.ident == ident:
                return line
        return None

    def get_item_for_refdes(self, refdes):
        for line in self.lines:
            if refdes in line.refdeslist:
                return GenericEntityBase(line.ident, refdes)

    def insert_component(self, item):
        assert isinstance(item, EntityBase)
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

    def _item_gen(self):
        for line in self.lines:
            for refdes in line.refdeslist:
                item = GenericEntityBase(line.ident, refdes)
                yield item

    @property
    def items(self):
        return self._item_gen()


class CompositeOutputBomLine(SourceableBomLineMixin):
    def __init__(self, line, colcount, parent=None):
        super(CompositeOutputBomLine, self).__init__()
        self._parent = parent
        self._ident = line.ident
        self.columns = [0] * colcount

    @property
    def ident(self):
        return self._ident

    @ident.setter
    def ident(self, value):
        self._ident = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def refdeslist(self):
        return [self._parent.get_col_title(x)
                for x, q in enumerate(self.columns) if q > 0]

    @staticmethod
    def _get_qty_str(qty):
        if isinstance(qty, NumericalUnitBase):
            return qty.integral_repr
        else:
            return str(qty)

    @property
    def collist(self):
        return [(self._parent.get_col_title(x),
                 self._get_qty_str(self.columns[x]))
                for x, q in enumerate(self.columns) if q > 0]

    @refdeslist.setter
    def refdeslist(self, value):
        raise NotImplementedError

    def add(self, line, column):
        """
        Add a BOM line to the COBOM

        :param line: The BOM line to insert
        :type line: :class:`OutputBomLine`
        :param column: The column to which the line should be added.
        :type column: int

        """
        if line.ident == self.ident:
            self.columns[column] = line.quantity
        else:
            logger.error("Ident Mismatch")

    @property
    def quantity(self):
        # Component output bom doesn't currently support multipliers.
        return self.uquantity

    @property
    def quantity_str(self):
        return self._get_qty_str(self.quantity)

    @property
    def uquantity(self):
        try:
            return sum(self.columns)
        except TypeError:
            raise TypeError(self.columns)

    def subset_qty(self, idxs):
        try:
            rval = 0
            for idx in idxs:
                rval += self.columns[idx]
            return rval
        except TypeError:
            raise TypeError(self.columns)

    def merge_line(self, cline):
        for idx, column in enumerate(self.columns):
            self.columns[idx] += cline.columns[idx]


class CompositeOutputBom(CostableBom):
    def __init__(self, bom_list, name=None):
        super(CompositeOutputBom, self).__init__()
        self.descriptors = []
        self.colcount = len(bom_list)
        self.descriptor = OutputElnBomDescriptor(None, None, name, None, 1)
        self._validation_context = ValidationContext(
            self.descriptor.configname, 'ICOBOM'
        )
        self.sourcing_policy = SourcingIdentPolicy(self._validation_context)
        self.validation_errors = ErrorCollector()

        i = 0
        for bom in bom_list:
            self._insert_bom(bom, i)
            i += 1
        self.sort_by_ident()

    @property
    def ident(self):
        return self.descriptor.configname

    def get_col_title(self, idx):
        return self.descriptors[idx].configname

    def get_subset_idxs(self, confignames):
        rval = []
        for configname in confignames:
            for idx, descriptor in enumerate(self.descriptors):
                if descriptor.configname == configname:
                    rval.append(idx)
        return rval

    def _insert_bom(self, bom, i):
        """
        Inserts a BOM into the COBOM.

        :param bom: The BOM to insert
        :type bom: :class:`OutputBom`
        :param i: The column to insert the BOM into
        :type i: int

        """
        self.descriptors.append(bom.descriptor)
        for line in bom.lines:
            self._insert_line(line, i)

    def _insert_line(self, line, i):
        """
        Inserts a BOM line into the COBOM

        :param line: The BOM line to insert
        :type line: :class:`OutputBomLine`
        :param i: The column to insert the BOM line into
        :type i: int

        """
        cline = self.find_by_ident(line.ident)
        if cline is None:
            cline = CompositeOutputBomLine(line, self.colcount, self)
            self.lines.append(cline)
        cline.add(line, i)

    def find_by_ident(self, ident):
        """
        Find a line in the COBOM for the given ident.

        :param ident: The ident to find in the COBOM
        :rtype: :class:`CompositeOutputBomLine`

        """
        for cline in self.lines:
            assert isinstance(cline, CompositeOutputBomLine)
            if cline.ident == ident:
                return cline
        return None

    def sort_by_ident(self):
        self.lines.sort(key=lambda x: x.ident, reverse=False)

    def dump(self, stream):
        writer = csv.writer(stream)
        writer.writerow(
            ['device'] +
            [x.configname + ' x' + str(x.multiplier)
             for x in self.descriptors] +
            ['Total'])
        for line in self.lines:
            columns = [None if x == 0 else x for x in line.columns]
            writer.writerow([line.ident] + columns + [line.quantity])

    def collapse_wires(self):
        for line in self.lines:
            device, value, footprint = parse_ident(line.ident)
            if device is None:
                continue
            if fpiswire(device):
                newident = device + ' ' + value
                newline = self.find_by_ident(newident)
                if newline is None:
                    line.ident = newident
                else:
                    newline.merge_line(line)
                    self.lines.remove(line)


class DeltaOutputBom(object):
    def __init__(self, start_bom, end_bom, reverse=False):
        self._start_bom = start_bom
        self._end_bom = end_bom
        self._is_reverse = reverse
        self._obom_add = None
        self._obom_sub = None
        self._descriptor = None
        self._gen_boms()

    @property
    def descriptor(self):
        return self._descriptor

    @staticmethod
    def _get_delta(original, target):
        delta = []
        for titem in target.items:
            oitem = original.get_item_for_refdes(titem.refdes)
            if oitem is None or oitem.ident != titem.ident:
                delta.append(titem)
        return delta

    def _gen_boms(self):
        if self._is_reverse:
            start_bom = self._end_bom
            end_bom = self._start_bom
        else:
            start_bom = self._start_bom
            end_bom = self._end_bom
        descriptor = OutputElnBomDescriptor(
                start_bom.descriptor.pcbname,
                end_bom.descriptor.cardfolder,
                '{0} -> {1}'.format(start_bom.descriptor.configname,
                                    end_bom.descriptor.configname),
                end_bom.descriptor.configurations)
        self._descriptor = descriptor
        self._obom_add = OutputBom(self._descriptor)
        self._obom_sub = OutputBom(self._descriptor)

        for item in self._get_delta(start_bom, end_bom):
            self._obom_add.insert_component(item)
        for item in self._get_delta(end_bom, start_bom):
            self._obom_sub.insert_component(item)

    @property
    def additions_bom(self):
        return self._obom_add

    @property
    def subtractions_bom(self):
        return self._obom_sub


def create_obom_from_listing(component_list, head):
    obom_descriptor = OutputElnBomDescriptor(head, None,
                                             head, None)
    obom = OutputBom(obom_descriptor)
    for line in component_list:
        device, value, footprint = parse_ident(line['ident'])
        from tendril.boms.electronics import EntityElnComp
        item = EntityElnComp()
        item.define('Undef', device, value, footprint)
        if device and fpiswire(device):
            length = Length(line['qty'])
            if length > 0:
                wireitem = EntityElnComp()
                wireitem.define(
                    'Undef', device, value, str(length)
                )
                obom.insert_component(wireitem)
        else:
            num = int(line['qty'])
            if num > 0:
                for i in range(num):
                    obom.insert_component(item)
    return obom


def load_cobom_from_file(f, name, tf=None, verbose=True, generic=False):
    bomlist = []
    header = []
    reader = csv.reader(f)
    for line in reader:
        line = [elem.strip() for elem in line]
        if line[0] == 'device':
            header = line
            break

    if verbose:
        logger.info('Inserting External Boms')
    oboms = []
    for head in header[1:-1]:
        if verbose:
            logger.info('Creating Bom : ' + head)
        obom_descriptor = OutputElnBomDescriptor(head,
                                                 None,
                                                 head, None)
        obom = OutputBom(obom_descriptor)
        oboms.append(obom)

    for line in reader:
        line = [elem.strip() for elem in line]
        if line[0] == '':
            continue
        if line[0] == 'END':
            break
        if tf and not tf.has_contextual_repr(line[0]):
            logger.warn('{0} Possibly not recognized'.format(line[0]))
        if tf:
            device, value, footprint = parse_ident(
                tf.get_canonical_repr(line[0]), generic=generic
            )
        else:
            device, value, footprint = parse_ident(line[0], generic=generic)
        logger.debug("Trying to insert line : " + line[0])
        # print base_tf.get_canonical_repr(line[0])
        from tendril.boms.electronics import EntityElnComp
        item = EntityElnComp()
        item.define('Undef', device, value, footprint)
        for idx, col in enumerate(line[1:-1]):
            if col != '':
                if device and fpiswire(device):
                    length = Length(col)
                    if length > 0:
                        wireitem = EntityElnComp()
                        wireitem.define(
                            'Undef', device, value, str(length)
                        )
                        oboms[idx].insert_component(wireitem)
                else:
                    num = int(col)
                    if num > 0:
                        for i in range(num):
                            oboms[idx].insert_component(item)

    for obom in oboms:
        if verbose:
            logger.info('Inserting External Bom : ' +
                        obom.descriptor.configname)
        bomlist.append(obom)
    cobom = CompositeOutputBom(
        bomlist,
        name=name
    )
    return cobom
