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
gEDA gsymlib Module (:mod:`tendril.gedaif.gsymlib`)
===================================================
"""


import os
import csv
import arrow
from future.utils import viewitems

import jinja2

import iec60063

from tendril.utils.config import GEDA_SYMLIB_ROOT
from tendril.utils.config import GEDA_SUBCIRCUITS_ROOT
from tendril.utils.config import AUDIT_PATH
from tendril.utils.config import TENDRIL_ROOT
from tendril.utils.config import INSTANCE_CACHE
from tendril.utils.config import MAKE_GSYMLIB_IMG_CACHE

from tendril.utils.fsutils import get_file_mtime
from tendril.utils.fsutils import VersionedOutputFile

from tendril.conventions.electronics import ident_transform
from tendril.conventions.electronics import fpismodlen
from tendril.conventions.electronics import fpiswire
from tendril.conventions.electronics import DEVICE_CLASSES
from tendril.conventions.electronics import construct_resistor
from tendril.conventions.electronics import construct_capacitor

from tendril.conventions.electronics import parse_capacitance
from tendril.conventions.electronics import parse_capacitor
from tendril.conventions.electronics import parse_resistance
from tendril.conventions.electronics import parse_resistor
from tendril.conventions.electronics import normalize_resistance

from tendril.utils.types.lengths import Length
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import Capacitance

from gschem import conv_gsch2png

from tendril.utils.files import yml as yaml
from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


class EDASymbolBase(object):
    def __init__(self):
        """
        Base class for EDA symbols. This class should not be used directly,
        but sub-classed per EDA suite, the sub-classes designed to interface
        with the way each EDA suite handles symbol libraries.

        .. todo::
            This class is to eventually move into a ``tendril.edaif`` module,
            which should be used to proxy to the specific implementation for
            the EDA suite being used.

        The constructor for this class should be called from it's subclasses
        after all the necessary implementation-specific variables are created
        and filled in.

        """
        self._device = ''
        self._value = ''
        self._footprint = ''
        self._status = None
        self._description = None
        self._package = None
        self._datasheet = None
        self._indicative_sourcing_info = None
        self._last_updated = None

        self._img_repr_path = None
        self._img_repr_fname = None

        self._get_sym()
        self._generate_img_repr()

    def _get_sym(self):
        raise NotImplementedError

    def _generate_img_repr(self):
        raise NotImplementedError

    # Core Properties
    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def footprint(self):
        return self._footprint

    @footprint.setter
    def footprint(self, value):
        self._footprint = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def package(self):
        return self._package

    @package.setter
    def package(self, value):
        self._package = value

    @property
    def last_updated(self):
        return self._last_updated

    @last_updated.setter
    def last_updated(self, value):
        self._last_updated = arrow.get(value)

    # Derived Properties
    @property
    def ident(self):
        return ident_transform(self.device, self.value, self.footprint)

    @property
    def ident_generic(self):
        return ident_transform(self.device, self.value, self.footprint,
                               generic=True)

    @property
    def is_wire(self):
        return fpiswire(self.device)

    @property
    def is_modlen(self):
        return fpismodlen(self.device)

    @property
    def img_repr_fname(self):
        return self._img_repr_fname

    @property
    def indicative_sourcing_info(self):
        if self._indicative_sourcing_info is None:
            self._indicative_sourcing_info = self.sourcing_info_qty(1)
        return self._indicative_sourcing_info

    def sourcing_info_qty(self, qty):
        from tendril.inventory.guidelines import electronics_qty
        from tendril.sourcing.electronics import get_sourcing_information
        from tendril.sourcing.electronics import SourcingException
        if fpiswire(self.device):
            iqty = Length(qty)
        else:
            iqty = qty
        iqty = electronics_qty.get_compliant_qty(self.ident, iqty)
        try:
            vsi = get_sourcing_information(self.ident, iqty,
                                           allvendors=True)
        except SourcingException:
            vsi = []
        return vsi

    @property
    def datasheet_url(self):
        if self._datasheet is not None:
            return self._datasheet
        for source in self.indicative_sourcing_info:
            if source.vpart.datasheet is not None:
                return source.vpart.datasheet

    @property
    def sym_ok(self):
        return self._validate()

    def _validate(self):
        if self.device not in DEVICE_CLASSES:
            return False
        return True

    # Status
    @property
    def is_virtual(self):
        if self.status == 'Virtual':
            return True
        return False

    @property
    def is_deprecated(self):
        if self.status == 'Deprecated':
            return True
        return False

    @property
    def is_experimental(self):
        if self.status == 'Experimental':
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


class GedaSymbol(EDASymbolBase):
    def __init__(self, fpath):
        """
        gEDA symbols use a symbol file, located within the gEDA component
        library folders, usually defined within a ``gafrc`` file. Only the
        symbol filename is important, and not it's location relative to the
        component library root.

        This class accepts a (full) file path to a gEDA symbol in it's
        constructor, and loads all the necessary detail abouts the symbol
        into itself.

        gEDA symbols may also represent a sub-circuit in a hierarchical
        schematic. Support for handling this type of use is included here.

        .. todo::
            Generator support is also built into this class for the moment.
            It should eventually be moved into :class:`EDASymbolBase` or a
            second base. It currently uses parameters seemingly specific
            gEDA, i.e., ``fpath`` and ``fname``. Handling single-file
            libraries such as those used by Eagle may need a more thought
            through approach.

        :param fpath: os path to the symbol file to be loaded
        """
        self.fpath = fpath
        self.fname = os.path.split(fpath)[1]

        self.source = ''
        self._sch_img_repr_path = None
        self._sch_img_repr_fname = None

        super(GedaSymbol, self).__init__()

    def _get_sym(self):
        self._acq_sym(self.fpath)
        if self.is_subcircuit:
            self._sch_img_repr()

    def _acq_sym(self, fpath):
        _last_updated = get_file_mtime(fpath)
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
                if line.startswith('source'):
                    self.source = line.split('=')[1].strip()
            if self.status == '':
                self.status = 'Active'

        if self.is_generator:
            _genftime = get_file_mtime(self.genpath)
            if not _genftime or _genftime > _last_updated:
                _last_updated = _genftime
        if self.is_subcircuit:
            _schftime = get_file_mtime(self.schematic_path)
            if not _last_updated or _schftime > _last_updated:
                _last_updated = _schftime
        self.last_updated = _last_updated

    def _generate_img_repr(self):
        outfolder = os.path.join(INSTANCE_CACHE, 'gsymlib')
        self._img_repr_fname = os.path.splitext(self.fname)[0] + '.png'
        self._img_repr_path = os.path.join(outfolder, self._img_repr_fname)
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        if os.path.exists(self._img_repr_path):
            if get_file_mtime(self._img_repr_path) > get_file_mtime(self.fpath):  # noqa
                return
        if MAKE_GSYMLIB_IMG_CACHE:
            conv_gsch2png(self.fpath, outfolder)

    def _sch_img_repr(self):
        outfolder = os.path.join(INSTANCE_CACHE, 'gsymlib')
        self._sch_img_repr_fname = self.source + '.png'
        self._sch_img_repr_path = os.path.join(outfolder,
                                               self._sch_img_repr_fname)
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        if os.path.exists(self._sch_img_repr_path):
            if get_file_mtime(self._sch_img_repr_path) > get_file_mtime(self.schematic_path):  # noqa
                return
        if MAKE_GSYMLIB_IMG_CACHE:
            conv_gsch2png(self.schematic_path, outfolder,
                          include_extension=True)

    # Validation
    def _validate(self):
        if self.is_subcircuit:
            if not self.source.endswith('.sch'):
                return False
            if not os.path.exists(self.schematic_path):
                return False
            return True
        return super(GedaSymbol, self)._validate()

    # Subcircuits
    @property
    def is_subcircuit(self):
        if self.source != '':
            return True
        return False

    @property
    def schematic_path(self):
        if not self.is_subcircuit:
            raise AttributeError
        return os.path.join(GEDA_SUBCIRCUITS_ROOT, self.source)

    @property
    def schematic_fname(self):
        if not self.is_subcircuit:
            raise AttributeError
        return self.source

    @property
    def subcircuitident(self):
        if not self.is_subcircuit:
            raise AttributeError
        return os.path.splitext(self.fname)[0]

    @property
    def sch_img_repr_fname(self):
        return self._sch_img_repr_fname

    # Generators
    @property
    def is_generator(self):
        if self.status == 'Generator':
            return True
        return False

    @property
    def genident(self):
        return os.path.splitext(self.fname)[0] + '.gen'

    @property
    def genpath(self):
        if self.is_generator:
            return os.path.splitext(self.fpath)[0] + '.gen.yaml'
        else:
            raise AttributeError

    @property
    def generator(self):
        if not self.is_generator:
            raise AttributeError
        return GSymGeneratorFile(self.fpath)

    @property
    def idents(self):
        if not self.is_generator:
            raise AttributeError
        if not self.generator.values:
            return None
        return [ident_transform(self.device, v, self.footprint)
                for v in self.generator.values]


class GSymGeneratorFile(object):
    def __init__(self, sympath):
        self._genpath = os.path.splitext(sympath)[0] + '.gen.yaml'
        self._sympath = sympath
        self._type = None
        self._ivalues = []
        self._igen = []
        self._iunits = []
        self._iseries = []
        data = self._get_data()
        self._values = []
        for value in data:
            if value is not None:
                self._values.append(value)

    @property
    def type(self):
        return self._type

    @property
    def igenerators(self):
        return self._igen

    @property
    def iseries(self):
        return self._iseries

    @property
    def ivalues(self):
        return self._ivalues

    @property
    def iunits(self):
        return self._iunits

    def _get_data(self):
        with open(self._genpath) as genfile:
            gendata = yaml.load(genfile)
        if gendata["schema"]["name"] == "gsymgenerator" and \
           gendata["schema"]["version"] == 1.0:

            if gendata['type'] == 'simple':
                self._type = 'Simple'
                self._ivalues = [v for v in gendata['values']
                                 if v is not None and v.strip() is not None]
                return gendata['values']
            values = []

            if gendata['type'] == 'resistor':
                self._type = 'Resistor'
                giseries = None
                for resistance in gendata['resistances']:
                    if resistance is not None:
                        values.append(resistance)
                        self._iunits.append(resistance)
                if 'composite_series' in gendata.keys():
                    from tendril.conventions.series import CustomValueSeries
                    try:
                        name = gendata['composite_series']['name']
                        tsymbol = GedaSymbol(self._sympath)
                        giseries = CustomValueSeries(
                            name, 'resistor', device=tsymbol.device,
                            footprint=tsymbol.footprint
                        )
                    except KeyError:
                        pass
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        self._igen.append(generator)
                        if generator['std'] == 'iec60063':
                            rvalues = iec60063.gen_vals(
                                generator['series'], iec60063.res_ostrs,
                                start=generator['start'], end=generator['end']
                            )
                            for rvalue in rvalues:
                                pval = construct_resistor(
                                    rvalue, generator['wattage']
                                )
                                values.append(pval)
                                if giseries is not None:
                                    giseries.add_value(rvalue, pval)
                        else:
                            raise ValueError
                if giseries is not None:
                    self._iseries.append(giseries)
                if 'values' in gendata.keys():
                    if gendata['values'][0].strip() != '':
                        values += gendata['values']
                        self._ivalues.extend(gendata['values'])
                if 'custom_series' in gendata.keys():
                    from tendril.conventions.series import CustomValueSeries
                    for name, series in viewitems(gendata['custom_series']):
                        if series['detail'].pop('type') != 'resistor':
                            raise ValueError('Expected a resistor series')
                        vals = series['values']
                        tsymbol = GedaSymbol(self._sympath)
                        iseries = CustomValueSeries(name, 'resistor',
                                                    device=tsymbol.device,
                                                    footprint=tsymbol.footprint)
                        for type_val, val in viewitems(vals):
                            iseries.add_value(type_val, val)
                        iseries._desc = series['detail'].pop('desc')
                        iseries._aparams = series['detail']
                        self._iseries.append(iseries)
                        values.extend(vals.values())
                return values

            if gendata['type'] == 'capacitor':
                self._type = 'Capacitor'
                giseries = None
                for capacitance in gendata['capacitances']:
                    if capacitance is not None:
                        values.append(capacitance)
                        self._iunits.append(capacitance)
                if 'composite_series' in gendata.keys():
                    from tendril.conventions.series import CustomValueSeries
                    try:
                        name = gendata['composite_series']['name']
                        tsymbol = GedaSymbol(self._sympath)
                        giseries = CustomValueSeries(
                            name, 'capacitor', device=tsymbol.device,
                            footprint=tsymbol.footprint
                        )
                    except KeyError:
                        pass
                if 'generators' in gendata.keys():
                    for generator in gendata['generators']:
                        self._igen.append(generator)
                        if generator['std'] == 'iec60063':
                            cvalues = iec60063.gen_vals(
                                generator['series'], iec60063.cap_ostrs,
                                start=generator['start'], end=generator['end']
                            )
                            for cvalue in cvalues:
                                pval = construct_capacitor(
                                    cvalue, generator['voltage']
                                )
                                values.append(pval)
                                if giseries is not None:
                                    giseries.add_value(cvalue, pval)
                        else:
                            raise ValueError
                if giseries is not None:
                    self._iseries.append(giseries)
                if 'values' in gendata.keys():
                    if gendata['values'][0].strip() != '':
                        values += gendata['values']
                        self._ivalues.append(gendata['values'])
                if 'custom_series' in gendata.keys():
                    from tendril.conventions.series import CustomValueSeries
                    for name, series in viewitems(gendata['custom_series']):
                        if series['detail'].pop('type') != 'resistor':
                            raise ValueError('Expected a resistor series')
                        vals = series['values']
                        tsymbol = GedaSymbol(self._sympath)
                        iseries = CustomValueSeries(name, 'resistor',
                                                    device=tsymbol.device,
                                                    footprint=tsymbol.footprint)
                        for type_val, val in viewitems(vals):
                            iseries.add_value(type_val, val)
                        iseries._desc = series['detail'].pop('desc')
                        iseries._aparams = series['detail']
                        self._iseries.append(iseries)
                        values.extend(vals.values())
                return values
            elif gendata['type'] == 'wire':
                for gauge in gendata['gauges']:
                    for color in gendata['colors']:
                        values.append('{0} {1}'.format(gauge, color))
                return values
        else:
            logger.ERROR("Config file schema is not supported")

    @property
    def values(self):
        if len(self._values) > 0:
            return self._values
        return None


def get_folder_symbols(path, template=None,
                       resolve_generators=True, include_generators=False):
    if template is None:
        template = _jinja_init()
    symbols = []
    files = [f for f in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]
    for f in files:
        if f.endswith(".sym"):
            symbol = GedaSymbol(os.path.join(path, f))
            if symbol.is_generator:
                generators.append(symbol)
                if include_generators is True:
                    symbols.append(symbol)
                if resolve_generators is True:
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
                if symbol.is_subcircuit:
                    subcircuits.append(symbol)
                symbols.append(symbol)
                # TODO This needs to be reimplemented in a cleaner form.
                if symbol.value.startswith('DUAL'):
                    nsymbol = GedaSymbol(symbol.fpath)
                    nsymbol.value = symbol.value.split(' ', 1)[1]
                    symbols.append(nsymbol)
    return symbols


def gen_symlib(path=GEDA_SYMLIB_ROOT, recursive=True,
               resolve_generators=True, include_generators=False):
    symbols = []
    template = _jinja_init()
    if recursive:
        for root, dirs, files in os.walk(path):
            symbols += get_folder_symbols(
                root, template,
                resolve_generators=resolve_generators,
                include_generators=include_generators
            )
    else:
        symbols = get_folder_symbols(
            path, template,
            resolve_generators=resolve_generators,
            include_generators=include_generators
        )
    return symbols


def gen_index(symlist, upper=False):
    lindex = {}
    for symbol in symlist:
        ident = symbol.ident_generic
        if upper:
            ident = ident.upper()
        if ident in lindex.keys():
            lindex[ident].append(symbol)
        else:
            lindex[ident] = [symbol]
    return lindex


def _jinja_init():
    templates_path = os.path.join(TENDRIL_ROOT, 'gedaif', 'templates')
    logger.debug("Loading templates from " + templates_path)
    loader = jinja2.FileSystemLoader(
        searchpath=templates_path
    )
    renderer = jinja2.Environment(loader=loader)
    template_file = 'generator.gen.yaml'
    template = renderer.get_template(template_file)
    return template


generators = []
subcircuits = []
custom_series = {}
gsymlib = []
index = {}
index_upper = {}
generator_names = []
subcircuit_names = []
gsymlib_idents = []


def regenerate_symlib():
    global generators
    generators = []
    global subcircuits
    subcircuits = []
    global gsymlib
    gsymlib = gen_symlib(GEDA_SYMLIB_ROOT)
    global index
    index = gen_index(gsymlib)
    global index_upper
    index_upper = gen_index(gsymlib, upper=True)
    global generator_names
    generator_names = [os.path.splitext(x.fname)[0] + '.gen'
                       for x in generators]
    global subcircuit_names
    subcircuit_names = [x.subcircuitident for x in subcircuits]
    global gsymlib_idents
    gsymlib_idents = set(index.keys())
    global custom_series
    custom_series = {}
    for sym in generators:
        for iseries in sym.generator.iseries:
            custom_series[iseries._name] = iseries

regenerate_symlib()


def get_generator(gen):
    for generator in generators:
        if os.path.splitext(generator.fname)[0] + '.gen' == gen:
            return generator


def get_subcircuit(sc):
    for subcircuit in subcircuits:
        if subcircuit.subcircuitident == sc:
            return subcircuit


def is_recognized(ident):
    if ident in gsymlib_idents:
        return True
    return False


def get_symbol(ident, case_insensitive=False, get_all=False):
    if case_insensitive is False:
        if ident in index.keys():
            if not get_all:
                return index[ident][0]
            else:
                return index[ident]
    else:
        if ident.upper() in index_upper.keys():
            if not get_all:
                return index_upper[ident.upper()][0]
            else:
                return index_upper[ident.upper()]
    raise NoGedaSymbolException(ident)


def get_symbol_folder(ident, case_insensitive=False):
    symobj = get_symbol(ident, case_insensitive=case_insensitive)
    sympath = symobj.fpath
    symfolder = os.path.split(sympath)[0]
    return os.path.relpath(symfolder, GEDA_SYMLIB_ROOT)


def get_latest_symbols(n=10, include_virtual=False):
    if include_virtual is False:
        tlib = [x for x in gsymlib if x.is_virtual is False]
    else:
        tlib = gsymlib
    slib = sorted(tlib, key=lambda y: y.last_updated, reverse=True)
    return slib[:n]


def find_capacitor(capacitance, footprint, device='CAP CER SMD', voltage=None):
    if isinstance(capacitance, str):
        try:
            capacitance = Capacitance(capacitance)
        except ValueError:
            raise NoGedaSymbolException(capacitance)
    if isinstance(capacitance, Capacitance):
        capacitance = capacitance._value
    if footprint[0:3] == "MY-":
        footprint = footprint[3:]
    for symbol in gsymlib:
        if symbol.device == device and symbol.footprint == footprint:
            cap, volt = parse_capacitor(symbol.value)
            sym_capacitance = parse_capacitance(cap)
            if capacitance == sym_capacitance:
                return symbol
    raise NoGedaSymbolException


def find_resistor(resistance, footprint, device='RES SMD', wattage=None):
    # TODO This should return a symbol instead, and usages should be adapted
    # accordingly to make consistent with find_capacitor
    if isinstance(resistance, str):
        try:
            resistance = Resistance(resistance)
        except ValueError:
            raise NoGedaSymbolException(resistance)
    if isinstance(resistance, Resistance):
        resistance = resistance._value
    if footprint[0:3] == "MY-":
        footprint = footprint[3:]
    if device == 'RES THRU':
        resistances = iec60063.gen_vals(iec60063.get_series('E24'),
                                        iec60063.res_ostrs)
        if resistance in [parse_resistance(x) for x in resistances]:
            return construct_resistor(normalize_resistance(resistance), '0.25W')  # noqa
        else:
            raise NoGedaSymbolException(resistance, device)
    for symbol in gsymlib:
        if symbol.device == device and symbol.footprint == footprint:
            res, watt = parse_resistor(symbol.value)
            sym_resistance = parse_resistance(res)
            if resistance == sym_resistance:
                return symbol.value
    raise NoGedaSymbolException(resistance)


def export_gsymlib_audit():
    auditfname = os.path.join(AUDIT_PATH, 'gsymlib-audit.csv')
    outf = VersionedOutputFile(auditfname)
    outw = csv.writer(outf)
    outw.writerow(['filename', 'status', 'ident', 'device', 'value',
                   'footprint', 'description', 'path', 'package'])
    for symbol in gsymlib:
        outw.writerow(
            [symbol.fname, symbol.status, symbol.ident, symbol.device,
             symbol.value, symbol.footprint, symbol.description,
             symbol.fpath, symbol.package]
        )
    outf.close()


class NoGedaSymbolException(Exception):
    pass
