"""
gEDA gsymlib Module documentation (:mod:`gedaif.gsymlib`)
=========================================================
"""

from utils.config import GEDA_SYMLIB_ROOT
import entityhub.conventions.electronics

import os
import csv


class GedaSymbol(object):
    def __init__(self, fpath):
        self.fpath = fpath
        self.fname = os.path.split(fpath)[1]
        self.device = ''
        self.value = ''
        self.footprint = ''
        self.description = ''
        self.status = ''
        self.package = ''
        self._acq_sym(fpath)

    def _acq_sym(self, fpath):
        with open(fpath, 'r') as f:
            for line in f.readlines():
                if line.startswith('device='):
                    self.device = line.split('=')[1].strip()
                if line.startswith('value='):
                    self.value = line.split('=')[1].strip()
                if line.startswith('footprint'):
                    self.footprint = line.split('=')[1].strip()
                    if self.footprint[0:3] == 'MY-':
                        self.footprint = self.footprint[3:]
                if line.startswith('description'):
                    self.description = line.split('=')[1].strip()
                if line.startswith('status'):
                    self.status = line.split('=')[1].strip()
                if line.startswith('package'):
                    self.package = line.split('=')[1].strip()

    @property
    def ident(self):
        return entityhub.conventions.electronics.ident_transform(self.device,
                                                                 self.value,
                                                                 self.footprint)

    @property
    def sym_ok(self):
        rval = False
        if self.device in entityhub.conventions.electronics.DEVICE_CLASSES:
            rval = True
        return rval


def gen_symlib():
    symbols = []
    for root, dirs, files in os.walk(GEDA_SYMLIB_ROOT):
        for f in files:
            if f.endswith(".sym"):
                symbols.append(GedaSymbol(os.path.join(root, f)))
    return symbols


def export_symlib():
    symbols = gen_symlib()
    with open('gsymlib.csv', 'w') as f:
        fw = csv.writer(f)
        fw.writerow(('filename', 'status', 'ident',
                     'device', 'value', 'footprint',
                     'description', 'path', 'package'))
        symbols.sort(key=lambda x: x.fpath)
        for symbol in symbols:
            fw.writerow((symbol.fname, symbol.status, symbol.ident,
                         symbol.device, symbol.value, symbol.footprint,
                         symbol.description, symbol.fpath, symbol.package))
        f.close()
