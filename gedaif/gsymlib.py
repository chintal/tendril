"""
gEDA gsymlib Module documentation (:mod:`gedaif.gsymlib`)
=========================================================
"""

import os
import csv
import logging

import yaml
import jinja2

from utils.config import GEDA_SYMLIB_ROOT
from utils.config import AUDIT_PATH
from utils.config import KOALA_ROOT


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
        self._is_virtual = ''
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
            if self.status == '':
                self.status = 'Active'

    @property
    def ident(self):
        return electronics.ident_transform(self.device,
                                                                 self.value,
                                                                 self.footprint)

    @property
    def sym_ok(self):
        rval = False
        if self.device in electronics.DEVICE_CLASSES:
            rval = True
        return rval

    @property
    def is_generator(self):
        if self.status == 'Generator':
            return True
        return False

    @property
    def is_virtual(self):
        if self.status == 'Virtual':
            return True
        return False

    @is_virtual.setter
    def is_virtual(self, value):
        if self.status == 'Generator':
            if value is True:
                self.status = 'Virtual'
        else:
            raise AttributeError


class GSymGeneratorFile(object):
    def __init__(self, sympath):
        self._genpath = os.path.splitext(sympath)[0] + '.gen.yaml'
        data = self._get_data()
        self._values = []
        for value in data:
            if value is not None:
                self._values.append(value)

    def _get_data(self):
        with open(self._genpath) as genfile:
            gendata = yaml.load(genfile)
        if gendata["schema"]["name"] == "gsymgenerator" and \
           gendata["schema"]["version"] == 1.0:

            if gendata['type'] == 'simple':
                return gendata['values']
            values = []

            if gendata['type'] == 'resistor':
                for wattage in gendata['wattages']:
                    for resistance in gendata['resistances']:
                        values.append(electronics.construct_resistor(resistance, wattage))
                return values

            if gendata['type'] == 'capacitor':
                for voltage in gendata['voltages']:
                    for capacitance in gendata['capacitances']:
                        values.append(electronics.construct_capacitor(capacitance, voltage))
                return values
        else:
            logging.ERROR("Config file schema is not supported")

    @property
    def values(self):
        if len(self._values) > 0:
            return self._values
        return None


def gen_symlib():
    symbols = []
    template = _jinja_init()
    for root, dirs, files in os.walk(GEDA_SYMLIB_ROOT):
        for f in files:
            if f.endswith(".sym"):
                symbol = GedaSymbol(os.path.join(root, f))
                if symbol.is_generator:
                    genpath = os.path.splitext(symbol.fpath)[0] + '.gen.yaml'
                    if os.path.exists(genpath):
                        genfile = GSymGeneratorFile(symbol.fpath)
                        values = genfile.values
                        if values is not None:
                            for value in values:
                                if value is not None:
                                    vsymbol = GedaSymbol(symbol.fpath)
                                    vsymbol.is_virtual = True
                                    vsymbol.value = value
                                    symbols.append(vsymbol)
                    else:
                        stage = {'symbolfile': os.path.split(symbol.fpath)[1],
                                 'value': symbol.value.strip(),
                                 'description': symbol.description}
                        with open(genpath, 'w') as gf:
                            gf.write(template.render(stage=stage))
                else:
                    symbols.append(symbol)
    return symbols


def _jinja_init():
    loader = jinja2.FileSystemLoader(searchpath=os.path.join(KOALA_ROOT, 'gedaif', 'templates'))
    renderer = jinja2.Environment(loader=loader)
    template_file = 'generator.gen.yaml'
    template = renderer.get_template(template_file)
    return template


def seed_generators():
    symlib = gen_symlib()
    template = _jinja_init()
    for symbol in symlib:
        if symbol.is_generator:
            genpath = os.path.splitext(symbol.fpath)[0] + '.gen.yaml'
            stage = {'symbolfile': os.path.split(symbol.fpath)[1],
                     'value': symbol.value.strip(),
                     'description': symbol.description}
            with open(genpath, 'w') as f:
                f.write(template.render(stage=stage))


def export_symlib():
    symbols = gen_symlib()

    with open(os.path.join(AUDIT_PATH, 'gsymlib-audit.csv'), 'w') as f:
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
