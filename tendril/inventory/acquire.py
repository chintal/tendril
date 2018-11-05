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
Inventory Acquire Module documentation (:mod:`inventory.acquire`)
=================================================================
"""

import csv
import datetime
import os
import re
from six import iteritems
from copy import copy
from requests.structures import CaseInsensitiveDict
from decimal import Decimal
from decimal import DecimalException

from tendril.entityhub import transforms
from tendril.gedaif import gsymlib
from tendril.utils import config
from tendril.utils import fsutils
from tendril.utils import log
from tendril.utils.files import libreoffice
from tendril.utils.connectors.tally.stock import TallyUnit
from tendril.utils.connectors.tally.stock import get_master
from tendril.utils.connectors.tally.stock import get_position
from tendril.utils.connectors.tally import TallyNotAvailable

try:
    from tendril.utils.types.lengths import Length
    from tendril.utils.types.mass import Mass
    from tendril.utils.types import ParseException
except ImportError:
    ParseException = DecimalException
    Length = Decimal
    Mass = Decimal


logger = log.get_logger(__name__, log.DEFAULT)


class MasterNotAvailable(Exception):
    pass


class InventoryReaderBase(object):
    def __init__(self, tfpath):
        self._tfpath = tfpath
        if os.path.isfile(tfpath):
            self._tf = transforms.TransformFile(self._tfpath)
        else:
            logger.warning("Transform File missing : " + self._tfpath)
            self._tf = None

    @property
    def row_gen(self):
        return self._row_gen()

    @property
    def tf_path(self):
        return self._tfpath

    @property
    def tf(self):
        return self._tf

    @property
    def tf_row_gen(self):
        return self._tf_row_gen()

    def _row_gen(self):
        raise NotImplementedError

    def _tf_row_gen(self):
        if not self.tf:
            raise LookupError
        for row in self.row_gen:
            yield (self.tf.get_canonical_repr(row[0]), row[1], row[2])

    def close(self):
        pass


class InventoryDBReader(InventoryReaderBase):
    def __init__(self, location, tfpath):
        super(InventoryDBReader, self).__init__(tfpath)


# Tally Reader Helper Functions
# TODO Move into staticmethods of the class itself
def _strip_unit(value, baseunit):
    return value.rstrip(baseunit.name)


def _rewrite_mass(value, baseunit):
    if isinstance(baseunit, TallyUnit):
        uname = baseunit.name
    else:
        uname = baseunit
    if uname.strip() == 'gm':
        value = value.replace(' gm', ' g')
    elif uname.strip() == 'grm':
        value = value.replace(' grm', ' g')
    elif uname.strip() == 'Kg':
        value = value.replace(' Kg', ' kg')
    return value


class InventoryTallyReader(InventoryReaderBase):
    exc = TallyNotAvailable

    def __init__(self, sname=None, location=None, company_name=None,
                 godown_name=None, tfpath=''):
        self._location = location
        self._sname = sname
        self._company_name = company_name
        self._godown_name = godown_name
        super(InventoryTallyReader, self).__init__(tfpath)

    _typeclass = CaseInsensitiveDict({
        'qty': (int, _strip_unit),
        'Pc':  (int, _strip_unit),
        'gm': (Mass, _rewrite_mass),
        'Kg': (Mass, _rewrite_mass),
        'grm': (Mass, _rewrite_mass),
        'ft': (Length, None),
        'cm': (Length, None),
        'Inch': (Length, None),
        'Feet': (Length, None),
        'meter': (Length, None),
        'mtr': (Length, None),
    })

    def _parse_quantity(self, value, item):
        masteritem = get_master(self._company_name).stockitems[item.name]
        additionalunits = masteritem.additionalunits
        baseunit = item.baseunits
        if not value:
            return 0
        if additionalunits:
            value = value.split('=')[0]
        value = value.strip()
        if baseunit.issimpleunit:
            unitname = baseunit.name.strip()
            if self._typeclass[unitname][1]:
                value = self._typeclass[unitname][1](value, baseunit)
            return self._typeclass[unitname][0](value)
        else:
            # Very ugly hacks
            uparts = baseunit.name.split(' of ')
            assert len(uparts) == 2
            uparts[1] = uparts[1].split()[1]
            if self._typeclass[uparts[0]][0] == self._typeclass[uparts[1]][0]:
                vparts = value.split(' ')
                plen = len(vparts) / 2
                assert plen * 2 == len(vparts)
                vpart0 = ' '.join(vparts[0:plen])
                if self._typeclass[uparts[0]][1]:
                    vpart0 = self._typeclass[uparts[0]][1](vpart0, uparts[0])
                rv = self._typeclass[uparts[0]][0](vpart0)
                vpart1 = ' '.join(vparts[plen:])
                if self._typeclass[uparts[1]][1]:
                    vpart1 = self._typeclass[uparts[1]][1](vpart1, uparts[1])
                rv += self._typeclass[uparts[1]][0](vpart1)
                return rv
        raise ValueError

    def _row_gen(self):
        position = get_position(self._company_name)
        for name, item in iteritems(position.stockitems):
            imaster = get_master(self._company_name).stockitems[name]
            try:
                # TODO Needs a godown filter here if the XML tags ever surface
                qty = self._parse_quantity(item.closingbalance, item)
                meta = {'name': name,
                        'godowns': [x.name for x in imaster.godowns],
                        'path': ' / '.join(imaster.parent.path) if imaster.parent else None}  # noqa
                yield name, qty, meta
            except (ParseException, ValueError):
                pass

    def dump(self):
        position = get_position(self._company_name)
        idx = 0
        for name, item in iteritems(position.stockitems):
            idx += 1
            try:
                qstring = '{3:4} {0:>10} {1:40} {2}'.format(
                    self._parse_quantity(item.closingbalance, item),
                    item.name, item.baseunits, idx
                )
                print(qstring)
            except (ParseException, ValueError, AssertionError) as e:
                master = get_master(self._company_name).stockitems[name]
                print(name, item.closingbalance, item.baseunits,
                      item.baseunits.issimpleunit, master.additionalunits, e)


class StockXlsReader(InventoryReaderBase):
    def __init__(self, xlf, sname, location, tfpath):
        """

            :type xlf: utils.ooutils.XLFile
            """
        super(StockXlsReader, self).__init__(tfpath)

        self.sheetname = sname
        assert isinstance(xlf, libreoffice.XLFile)
        self._xlf = xlf
        self.filepath = xlf.fpath
        self.qtydate = None
        self._csvpath = xlf.get_csv_path(sname)
        self._csvfile = open(self._csvpath, 'rb')
        self._csvreader = csv.reader(self._csvfile)
        self._colident = 0
        self._colqty = -1
        self._skip_to_header()

    def _skip_to_header(self):
        for row in self._csvreader:
            if row[0].strip() == 'Device':
                self._get_cols(row)
                break

    def _get_cols(self, row):
        for (index, item) in enumerate(row):
            result = self._is_balance(item)
            if result is not None:
                self._colqty = index
                self.qtydate = result

    @staticmethod
    def _is_balance(item):
        if item.strip().startswith('Balance on'):
            match = re.search(r'\d{2}/\d{2}/\d{4}', item)
            try:
                date = datetime.datetime.strptime(
                    match.group(), '%d/%m/%Y').date()
            except AttributeError:
                logger.debug(
                    "Mangled Balance Column. Tried to match :" + item
                )
                return None
            return date
        return None

    def _row_gen(self):
        for row in self._csvreader:
            if row[0].strip() == '':
                continue
            if row[0].strip() == 'END':
                continue
            try:
                qty = int(row[self._colqty])
            except ValueError:
                try:
                    qty = float(row[self._colqty])
                except ValueError:
                    logger.error("Could not parse quantity for ident {0} {1}"
                                 "".format(row[self._colident],
                                           row[self._colqty]))
                    qty = 0
            yield (row[self._colident], qty, None)

    def close(self):
        self._csvfile.close()


def get_reader(elec_inven_data_idx):
    sdict = copy(config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx])
    reader = None
    invtype = sdict.pop('type')
    if invtype == 'QuazarStockXLS':
        if not os.path.isabs(sdict['fpath']):
            sdict['fpath'] = config.get_svn_path(sdict['fpath'])
        sdict['xlf'] = libreoffice.get_xlf(sdict.pop('fpath'))
        reader = StockXlsReader(**sdict)
    elif invtype == 'TallyStock':
        reader = InventoryTallyReader(**sdict)
    if reader is not None:
        return reader
    else:
        logger.error("Could not find reader for: "
                     "ELECTRONICS_INVENTORY_DATA." +
                     str(elec_inven_data_idx))


def gen_canonical_transform(elec_inven_data_idx, regen=True):
    # TODO Support Unified Transforms?
    reader = get_reader(elec_inven_data_idx)
    if not reader:
        return
    outp = reader.tf_path
    outf = fsutils.VersionedOutputFile(outp)
    outw = csv.writer(outf)
    outw.writerow(
        ('Current', 'gEDA Current', 'Ideal', 'Status', 'In Symlib')
    )
    for line in reader.row_gen:
        if regen and reader.tf.has_contextual_repr(line[0]):
            if gsymlib.is_recognized(reader.tf.get_canonical_repr(line[0])):
                in_symlib = 'YES'
            else:
                in_symlib = ''
            outw.writerow((line[0],
                           reader.tf.get_canonical_repr(line[0]),
                           reader.tf.get_ideal_repr(line[0]),
                           reader.tf.get_status(line[0]),
                           in_symlib,))
        else:
            if gsymlib.is_recognized(line[0]):
                in_symlib = True
            else:
                in_symlib = False
            outw.writerow((line[0], line[0], line[0], 'NEW', in_symlib))
    outf.close()


if __name__ == "__main__":
    pass
