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
from copy import copy

from tendril.entityhub import transforms
from tendril.gedaif import gsymlib
from tendril.utils import config
from tendril.utils import fsutils
from tendril.utils import log
from tendril.utils.files import libreoffice

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
        from tendril.utils.connectors.tally.stock import InventoryTallyReader
        reader = InventoryTallyReader(**sdict)
    if reader is not None:
        return reader
    else:
        logger.error("Could not find reader for: "
                     "ELECTRONICS_INVENTORY_DATA." +
                     str(elec_inven_data_idx))


def gen_canonical_transform(elec_inven_data_idx, regen=True):
    sdict = copy(config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx])
    invtype = sdict.pop('type')
    reader = None
    if invtype == 'QuazarStockXLS':
        if not os.path.isabs(sdict['fpath']):
            sdict['fpath'] = config.get_svn_path(sdict['fpath'])
        sdict['xlf'] = libreoffice.get_xlf(sdict.pop('fpath'))
        reader = StockXlsReader(**sdict)
    elif invtype == 'TallyStock':
        from tendril.utils.connectors.tally.stock import InventoryTallyReader
        reader = InventoryTallyReader(**sdict)
    if not reader:
        return
    outp = sdict['tfpath']
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
