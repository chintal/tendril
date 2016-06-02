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

import json
import csv
from future.utils import viewitems

from tendril.entityhub.entitybase import EntityBase
from tendril.entityhub.entitybase import GenericEntityBase
from tendril.conventions.electronics import fpiswire
from tendril.conventions.electronics import parse_ident
from tendril.inventory.guidelines import electronics_qty
from tendril.gedaif.gsymlib import get_symbol
from tendril.gedaif.gsymlib import NoGedaSymbolException
from tendril.utils import log
from tendril.utils.types.lengths import Length
from tendril.utils.types.currency import native_currency_defn

from .validate import ValidationContext
from .validate import ErrorCollector
from .validate import IdentErrorBase
from .validate import ValidationPolicy


logger = log.get_logger(__name__, log.DEFAULT)


class SourcingIdentPolicy(ValidationPolicy):
    def __init__(self, context):
        super(SourcingIdentPolicy, self).__init__(context)
        self.is_error = True


class SourcingIdentNotRecognized(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotRecognized, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotRecognized {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' is not a recognized component."
                        "".format(self.ident),
            'detail': "This component is not recognized by the library and "
                      "is therefore not sourceable. Component not included "
                      "in costing analysis. Used by refdes {0}"
                      "".format(', '.join(self.refdeslist)),
        }


class SourcingIdentNotSourceable(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotSourceable, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotSourceable {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' is not sourceable."
                        "".format(self.ident),
            'detail': "Viable sources for this component are not known. "
                      "Component not included in costing analysis. Used by "
                      "refdes {0}".format(', '.join(self.refdeslist)),
        }


class OBomCostingBreakup(object):
    def __init__(self, name):
        self._name = name
        self._currency_symbol = native_currency_defn.symbol
        self._devices = {}
        self._total_cost = 0

    def insert(self, ident, cost):
        d, v, f = parse_ident(ident)
        if d not in self._devices.keys():
            self._devices[d] = []
        self._devices[d].append(
            {'name': ident,
             'size': cost.native_value}
        )
        self._total_cost += cost

    def sort(self):
        for d in self._devices.keys():
            self._devices[d].sort(key=lambda x: x['size'], reverse=True)

    @property
    def total_cost(self):
        return self._total_cost

    @property
    def currency_symbol(self):
        return self._currency_symbol

    @property
    def content(self):
        return [{'name': k, 'children': v}
                for k, v in viewitems(self._devices)]

    @property
    def json(self):
        return json.dumps(
            {'name': self._name,
             'children': [
                 {'name': k, 'children': v} for k, v in
                 sorted(viewitems(self._devices),
                        key=lambda x: sum(y['size'] for y in x[1]),
                        reverse=True)
                 ]
             }
        )


class HierachicalCostingBreakup(object):
    def __init__(self, name):
        self._name = name
        self._currency_symbol = native_currency_defn.symbol
        self._sections = {}

    def insert(self, ident, breakup):
        if ident not in self._sections.keys():
            self._sections[ident] = breakup
        else:
            raise ValueError('ident already in sections')

    @property
    def currency_symbol(self):
        return self._currency_symbol

    @property
    def content(self):
        raise NotImplementedError

    @property
    def json(self):
        return json.dumps(
            {'name': self._name,
             'children': [
                 {'name': k, 'children': v.content} for k, v in
                 sorted(viewitems(self._sections),
                        key=lambda x: x[1].total_cost,
                        reverse=True)
                 ]
             }
        )


class NoStructureHereException(Exception):
    pass


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


class OutputBomLine(object):
    def __init__(self, comp, parent):
        assert isinstance(comp, EntityBase)
        self.ident = comp.ident
        self.refdeslist = []
        self.parent = parent
        self._isinfo = ''
        self._sourcing_exception = None

    def add(self, comp):
        assert isinstance(comp, EntityBase)
        if hasattr(comp, 'fillstatus'):
            if comp.fillstatus == "DNP":
                return
            if comp.fillstatus == "CONF":
                logger.warning("Configurable Component "
                               "not Configured by Conf File : " + comp.refdes)
        if comp.ident == self.ident:
            self.refdeslist.append(comp.refdes)
        else:
            logger.error("Ident Mismatch")
            raise Exception

    @property
    def uquantity(self):
        device, value, footprint = parse_ident(self.ident)
        if device is None:
            logger.warning("Device not identified : " + self.ident)
        elif fpiswire(device):
            try:
                elen = Length(footprint) * 10 / 100
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
        return self.uquantity * self.parent.descriptor.multiplier

    def _get_isinfo(self):
        # qty = electronics_qty.get_compliant_qty(self.ident, self.quantity)
        if self.ident.startswith('PCB'):
            from tendril.entityhub.modules import get_pcb_lib
            pcblib = get_pcb_lib()
            ident = self.ident[len('PCB '):]
            if ident in pcblib.keys():
                symbol = pcblib[ident]
            else:
                self._isinfo = None
                self._sourcing_exception = SourcingIdentNotRecognized(
                    self.parent.sourcing_policy, self.ident, self.refdeslist
                )
                return
        else:
            try:
                symbol = get_symbol(self.ident)
            except NoGedaSymbolException:
                self._isinfo = None
                self._sourcing_exception = SourcingIdentNotRecognized(
                    self.parent.sourcing_policy, self.ident, self.refdeslist
                )
                return
        try:
            self._isinfo = symbol.indicative_sourcing_info[0]
        except IndexError:
            self._isinfo = None
            self._sourcing_exception = SourcingIdentNotSourceable(
                self.parent.sourcing_policy, self.ident, self.refdeslist
            )

    @property
    def isinfo(self):
        if self._isinfo == '':
            self._get_isinfo()
        return self._isinfo

    @property
    def indicative_cost(self):
        if self.isinfo is not None:
            qty = electronics_qty.get_compliant_qty(self.ident, self.quantity)
            ubprice, nbprice = self.isinfo.vpart.get_price(qty)
            if ubprice is not None:
                price = ubprice
            elif nbprice is not None:
                price = nbprice
            else:
                price = self.isinfo.ubprice
            effprice = self.isinfo.vpart.get_effective_price(price)
            return effprice.extended_price(self.uquantity, allow_partial=True)
        else:
            return None

    @property
    def sourcing_error(self):
        if self._isinfo == '':
            self._get_isinfo()
        return self._sourcing_exception

    def __repr__(self):
        return "{0:<50} {1:<4} {2}".format(
            self.ident, self.quantity, str(self.refdeslist)
        )


class OutputBom(object):
    def __init__(self, descriptor):
        """

        :type descriptor: outputbase.OutputElnBomDescriptor
        """
        self.lines = []
        self.descriptor = descriptor
        if self.descriptor.groupname is not None:
            locality = 'OBOM.{0}'.format(self.descriptor.groupname)
        else:
            locality = 'OBOM'
        self._validation_context = ValidationContext(
            self.descriptor.configname, locality
        )
        self.validation_errors = ErrorCollector()
        self.sourcing_policy = SourcingIdentPolicy(self._validation_context)
        self._sourcing_errors = None
        self._indicative_cost = None
        self._indicative_cost_breakup = None

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

    @property
    def indicative_cost(self):
        if self._indicative_cost is None:
            self._indicative_cost = 0
            for line in self.lines:
                lcost = line.indicative_cost
                if lcost is not None:
                    self._indicative_cost += lcost
        return self._indicative_cost

    def _build_indicative_cost_breakup(self):
        self._indicative_cost_breakup = \
            OBomCostingBreakup(self.descriptor.configname)
        for line in self.lines:
            lcost = line.indicative_cost
            if lcost is not None:
                self._indicative_cost_breakup.insert(line.ident, lcost)
        self._indicative_cost_breakup.sort()

    @property
    def indicative_cost_breakup(self):
        if self._indicative_cost_breakup is None:
            self._build_indicative_cost_breakup()
        return self._indicative_cost_breakup

    @property
    def sourcing_errors(self):
        if self._sourcing_errors is None:
            self._sourcing_errors = ErrorCollector()
            for line in self.lines:
                if line.sourcing_error is not None:
                    self._sourcing_errors.add(line.sourcing_error)
        return self._sourcing_errors


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


class CompositeOutputBomLine(object):
    def __init__(self, line, colcount):
        self.ident = line.ident
        self.columns = [0] * colcount

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


class CompositeOutputBom(object):
    def __init__(self, bom_list, name=None):
        self.descriptors = []
        self.lines = []
        self.colcount = len(bom_list)
        self.descriptor = OutputElnBomDescriptor(None, None, name, None, 1)
        i = 0
        for bom in bom_list:
            self._insert_bom(bom, i)
            i += 1
        self.sort_by_ident()

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
            cline = CompositeOutputBomLine(line, self.colcount)
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
