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

import conventions.electronics
import conventions.iec60063


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
        return conventions.electronics.ident_transform(self.device,
                                                       self.value,
                                                       self.footprint)

    @property
    def sym_ok(self):
        rval = False
        if self.device in conventions.electronics.DEVICE_CLASSES:
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

    def __repr__(self):
        return '{0:40}'.format(self.ident)


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
                for resistance in gendata['resistances']:
                    values.append(resistance)
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        if generator['std'] == 'iec60063':
                            rvalues = conventions.iec60063.gen_vals(generator['series'],
                                                                    conventions.iec60063.res_ostrs,
                                                                    start=generator['start'],
                                                                    end=generator['end'])
                            for rvalue in rvalues:
                                values.append(conventions.electronics.construct_resistor(rvalue, generator['wattage']))
                        else:
                            raise ValueError

                return values

            if gendata['type'] == 'capacitor':
                for capacitance in gendata['capacitances']:
                        values.append(capacitance)
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        if generator['std'] == 'iec60063':
                            cvalues = conventions.iec60063.gen_vals(generator['series'],
                                                                    conventions.iec60063.cap_ostrs,
                                                                    start=generator['start'],
                                                                    end=generator['end'])
                            for cvalue in cvalues:
                                values.append(conventions.electronics.construct_capacitor(cvalue, generator['voltage']))
                        else:
                            raise ValueError

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


gsymlib = gen_symlib()


def find_capacitor(capacitance, footprint, device='CAP CER SMD', voltage=None):
    for symbol in gsymlib:
        if symbol.device == device and symbol.footprint == footprint:
            cap, volt = conventions.electronics.parse_capacitor(symbol.value)
            sym_capacitance = conventions.electronics.parse_capacitance(cap)
            if capacitance == sym_capacitance:
                return symbol
    raise ValueError
