"""
Inventory Acquire Module documentation (:mod:`inventory.acquire`)
=================================================================
"""

import utils.libreoffice
import utils.fs
import utils.config

import entityhub.transforms

import os
import csv
import re
import datetime
import logging


class StockXlsReader(object):
    def __init__(self, xlf, sname, location, tfpath):
        """

        :type xlf: utils.ooutils.XLFile
        """
        self.location = location
        self.sheetname = sname
        assert isinstance(xlf, utils.libreoffice.XLFile)
        self._xlf = xlf
        self.filepath = xlf.fpath
        self.qtydate = None

        self._csvpath = xlf.get_csv_path(sname)
        self._csvfile = open(self._csvpath, 'rb')
        self._csvreader = csv.reader(self._csvfile)
        self._colident = 0
        self._colqty = -1

        self._tfpath = tfpath
        self.tf = None
        if os.path.isfile(tfpath):
            self.tf = entityhub.transforms.TransformFile(self._tfpath)
        else:
            logging.warning("Transform File missing : " + self._tfpath)

        self._skip_to_header()
        self.row_gen = self._row_gen()
        self.tf_row_gen = self._tf_row_gen()

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
        if 'Balance on' in item:
            match = re.search(r'\d{2}/\d{2}/\d{4}', item)
            date = datetime.datetime.strptime(match.group(), '%d/%m/%Y').date()
            return date
        return None

    def _row_gen(self):
        for row in self._csvreader:
            if row[0].strip() == '':
                continue
            if row[0].strip() == 'END':
                continue
            yield (row[self._colident],
                   row[self._colqty])
        self._csvfile.close()

    def _tf_row_gen(self):
        for row in self.row_gen:
            yield (self.tf.get_canonical_repr(row[0]),
                   row[1])
        self._csvfile.close()


def get_stockxlsreader(xlpath, sname, location, tfpath):
    xlf = utils.libreoffice.get_xlf(xlpath)
    reader = StockXlsReader(xlf, sname, location, tfpath)
    return reader


def get_reader(elec_inven_data_idx):
    sdict = utils.config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx]
    reader = None
    if sdict['type'] == 'QuazarStockXLS':
        fpath = sdict['fpath']
        sname = sdict['sname']
        location = sdict['location']
        tfpath = sdict['tfpath']
        reader = get_stockxlsreader(fpath, sname, location, tfpath)

    if reader is not None:
        return reader
    else:
        logging.error("Could not find reader for: ELECTRONICS_INVENTORY_DATA."
                      + str(elec_inven_data_idx))


def gen_canonical_transform(elec_inven_data_idx):
    sdict = utils.config.ELECTRONICS_INVENTORY_DATA[elec_inven_data_idx]
    if sdict['type'] == 'QuazarStockXLS':
        fpath = sdict['fpath']
        sname = sdict['sname']
        location = sdict['location']
        tfpath = sdict['tfpath']

        rdr = get_stockxlsreader(fpath, sname, location, tfpath)

        outp = tfpath
        outf = utils.fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Current', 'gEDA Current', 'Ideal'))
        for line in rdr.row_gen:
            outw.writerow((line[0], line[0], line[0]))
        outf.close()


def helper_transform(ident):
    """

    :type ident: str
    """
    cident = ident
    if ident.startswith(('CAP CER SMD', 'RES SMD')):
        if ident.endswith('0805'):
            cident = ident
        elif ident.endswith(('F', 'E', 'K', 'M')):
            cident = ident + ' 0805'
        else:
            logging.warning("Possibly Malformed ident : " + ident)
            cident = ident
    if ident.startswith(('CRYSTAL 2PIN')):
        if ident.endswith('HC49'):
            cident = ident
        elif ident.endswith(('Hz')):
            cident = ident + ' HC49'
        else:
            logging.warning("Possibly Malformed ident : " + ident)
            cident = ident
    return cident


if __name__ == "__main__":
    pass
