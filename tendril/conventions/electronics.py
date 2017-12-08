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
Electronics Conventions Module documentation (:mod:`conventions.electronics`)
=============================================================================
"""

import logging
import re

from copy import copy
from collections import namedtuple

from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import Capacitance
from tendril.utils.types.electromagnetic import Voltage
from tendril.utils.types.thermodynamic import ThermalDissipation
from tendril.utils.types.unitbase import Tolerance
from tendril.utils.types.unitbase import NumericalUnitBase
from tendril.utils.types import ParseException


DEVICE_CLASSES_DOC = [
    ('RES SMD', 'SMD Resistors'),
    ('RES THRU', 'THRU Resistors'),
    ('RES POWER', 'Off-PCB power resistors for direct mounting onto heatsinks'),
    ('RES ARRAY THRU', 'THRU Resistor Arrays'),
    ('RES ARRAY SMD', 'SMD Resistor Arrays'),
    ('POT TRIM', 'Trimpots'),
    ('POT DIAL', 'Dial Pots'),
    ('VARISTOR', 'Varistors and MOVs'),
    ('CAP CER SMD', 'SMD Ceramic Capacitors'),
    ('CAP MICA SMD', 'SMD Mica Capacitors'),
    ('CAP TANT SMD', 'SMD Tantalum Capacitors'),
    ('CAP TANT THRU', 'THRU Tantalum Capacitors'),
    ('CAP CER THRU', 'THRU Ceramic Capacitors'),
    ('CAP ELEC THRU', 'THRU Electrolytic Capacitors'),
    ('CAP AL SMD', 'SMD Aluminum Electrolytic and Polymer Capacitors'),
    ('CAP POLY THRU', 'THRU Poly Capacitors'),
    ('CAP PAPER THRU', 'THRU Paper Capacitors'),
    ('INDUCTOR SMD', 'SMD Inductors'),
    ('INDUCTOR THRU', 'THRU Inductors'),
    ('FERRITE BEAD SMD', 'SMD Ferrite Beads'),
    ('TRANSFORMER HEAVY', 'Transformers'),
    ('TRANSFORMER SMD', 'SMD Transformers'),
    ('DIODE SMD', 'SMD Diodes'),
    ('DIODE THRU', 'THRU Diodes'),
    ('ZENER SMD', 'SMD Zener Diodes'),
    ('ZENER THRU', 'THRU Zener Diodes'),
    ('TRIAC', 'Triacs'),
    ('LED SMD', 'SMD LEDs'),
    ('LED THRU', 'THRU LEDs'),
    ('LED MODULE', 'LED Modules'),
    ('BRIDGE RECTIFIER', 'Bridge Rectifiers'),
    ('CRYSTAL AT', 'AT cut Crystals'),
    ('CRYSTAL TF', 'Tuning Fork Crystals'),
    ('CRYSTAL OSC', 'Integrated Crystal Oscillators'),
    ('CRYSTAL VCXO', 'Voltage Controlled Crystal Oscillators'),
    ('TRANSISTOR THRU', 'THRU Transistors'),
    ('TRANSISTOR SMD', 'SMD Transistors'),
    ('MOSFET THRU', 'THRU MOSFETs'),
    ('MOSFET SMD', 'SMD MOSFETs'),
    ('IC THRU', 'THRU Hole ICs'),
    ('IC DIP', '(Phase out) THRU Hole ICs'),
    ('IC SMD', 'SMD ICs'),
    ('IC PLCC', 'PLCC ICs, separated because of their need for a socket'),
    ('IC POWER', 'Off-PCB power ICs for direct mounting onto heatsinks'),
    ('SOCKET STRIP', 'SIP sockets'),
    ('SOCKET DIP', 'IC sockets and bases'),
    ('RELAY', 'Relays'),
    ('MODULE SMPS', 'OTS Prefabricated SMPS Modules'),
    ('MODULE LCD', 'LCDs'),
    ('MODULE', 'Modules'),
    ('PCB EDGE', 'Printed Circuit Board Edges'),
    ('PCB', 'Printed Circuit Board'),
    ('BUZZER', 'Buzzers'),
    ('CONN CIRCULAR', 'Circular Connectors'),
    ('CONN BNC', 'BNC Connectors'),
    ('CONN SMA', 'SMA Connectors'),
    ('CONN BANANA', 'Banana Connectors'),
    ('CONN BERG STRIP', 'Berg Strips'),
    ('CONN TERMINAL DMC', 'Phoenix Contact DMC series PCB mount Terminals'),
    ('CONN TERMINAL BLOCK', 'Terminal Blocks, usually single-part'),
    ('CONN TERMINAL', 'Terminal Connectors, usually two-part.'),
    ('CONN DTYPE HOOD', 'Hood for DTYPE Connectors'),
    ('CONN DTYPE', 'DTYPE Connectors'),
    ('CONN INTERBOARD', 'Stackthrough Headers'),
    ('CONN FRC', 'FRC Connectors'),
    ('CONN MINIDIN', 'MiniDIN Connectors'),
    ('CONN MOLEX MINIFIT', 'Molex Minifit connectors'),
    ('CONN MOLEX', 'Molex Connector'),
    ('CONN SECII', 'TE SEC-II Backplane Connectors'),
    ('CONN EDGERATE', 'Samtec Edgerate (HSEC8) Backplane Connectors'),
    ('CONN BARREL', 'DC Power Jacks and similar barrel connectors'),
    ('CONN SIP', 'SIP connectors'),
    ('CONN STEREO', 'Stereo Connectors'),
    ('CONN DF13 HOUS', 'Hirose DF13 Connector Housings'),
    ('CONN DF13 WIRE', 'Prefabricated Hirose DF13 Connector Wires'),
    ('CONN DF13 CRIMP', 'Hirose DF13 Connector Crimps'),
    ('CONN DF13', 'Hirose DF13 PCB Mount Connectors'),
    ('CONN MODULAR', 'Modular Connectors'),
    ('CONN USB', 'USB Connectors'),
    ('CONN THC', 'Thermocouple Connectors'),
    ('SWITCH TACT', 'Tactile Switches'),
    ('SWITCH PUSHBTN', 'Pushbutton Switches'),
    ('SWITCH ROCKER', 'Rocker Switches'),
    ('TESTPOINT', 'Test Points'),
    ('SOLDER DOT', 'Solder Dots'),
    ('BATTERY', 'Battery and Battery Holders'),
    ('HEAT SINK', 'Heat Sinks'),
    ('CABLE FRC', 'FRC Cables'),
    ('CABLE SIP SSC', 'Prefabricated SIP Cables'),
    ('CABLE MARKER', 'Cable Markers'),
    ('CABLE ROUND SHLD', 'Round Shielded Cables'),
    ('WIRE INSULATED', 'Insulated Wires'),
    ('WIRE TEFLON INSULATED', 'Teflon Insulated Wires'),
    ('WIRE THERMOCOUPLE', 'Thermocouple Wires'),
    ('WIRE LAMINATED COPPER', 'Laminated Copper Wires'),
    ('SLEEVE SHRINK', 'Heat shrinking sleeves'),
    ('CRIMP', 'Crimps'),
    ('THIMBLE', 'Thimbles'),
    ('FUSE HOLDER', 'Fuse Holders'),
    ('FUSE', 'Fuses'),
    ('FAN', 'Fans'),
    ('POWER CORD', 'Power Cords'),
    ('USB CABLE', 'USB Cables'),
    ('RTD', 'Temperature Dependent Resistors'),
    ('SOCKET POWER', 'Power Sockets'),
    ('SOCKET ZIF', 'Zero Insertion Force IC Sockets'),
    ('SOCKET SPECIAL', 'Specialized Sockets'),
    ('LIGHT PIPE', 'Light Pipes'),
]


DEVICE_CLASSES = [x[0] for x in DEVICE_CLASSES_DOC]

nofp_strs = {"PCB", "PCB EDGE", "CONN", "MODULE", "CRYSTAL OSC", "HEAT SINK",
             "SOCKET POWER", "FUSE", "SWITCH PUSHBTN",
             "SWITCH ROCKER", "TRANSFORMER HEAVY", "CRIMP", "THIMBLE",
             "CABLE MARKER", "POWER CORD", "USB CABLE", "SOCKET SPECIAL"}

nofp_pattern = r"^(?:%s)" % '|'.join(nofp_strs)
rex_nofp = re.compile(nofp_pattern)


fpiswire_strs = {"CABLE ROUND", "WIRE", "CABLE FRC", "SLEEVE SHRINK"}

wire_pattern = r"^(?:%s)" % '|'.join(fpiswire_strs)
rex_wire = re.compile(wire_pattern)


fpismodlen_strs = {"CABLE SIP SSC", "CONN DF13 WIRE"}

modlen_pattern = r"^(?:%s)" % '|'.join(fpismodlen_strs)
rex_modlen = re.compile(modlen_pattern)


def no_fp(device):
    if not device:
        return False
    if rex_nofp.match(device):
        return True
    return False


def fpismodlen(device):
    if not device:
        return False
    if rex_modlen.match(device):
        return True
    return False


def fpiswire(device):
    if not device:
        return False
    if rex_wire.match(device):
        return True
    return False


def fpiswire_ident(ident):
    device, value, footprint = parse_ident(ident)
    if fpiswire(device):
        return True
    return False


def ident_transform(device, value, footprint, tf=None, generic=False):
    """
    Auto-generated ident string from the component ``device``, ``value``
    and ``footprint`` attributes.

    If the device string starts with any of the strings in ``nofp_strings``,
    the ``footprint`` is excluded from the ``ident`` string.

    When applied to gEDA generated data (BOMs, gsymlib), the return value is
    the ``Canonical Representation`` for the component. The burden of ensuring
    uniqueness and consistency is on the gEDA schematic files and authors
    thereof. See conventions.rst listed in ``somewhere`` for relevant
    guidelines.

    For all other forms of data, the specific modules must provide a transform
    csv file to ensure correct mapping into the canonical form. For the format
    of this file, see ``somewhere``.

    :type device: str
    :type value: str
    :type footprint: str
    """

    try:
        ident = device + " " + value + " " + footprint
    except TypeError:
        logging.error(
            'Error generating ident : ' +
            str(device) + ' ' + str(value) + ' ' + str(footprint)
        )
        ident = 'FATAL'
    if device is None:
        logging.critical("Malformed ident : " + ident)
    else:
        if no_fp(device):
            ident = device + " " + value
        if generic is True and fpiswire(device):
            ident = device + " " + value
    if tf is None:
        return ident
    else:
        return tf.get_canonical(tf)


class MalformedIdentError(ValueError):
    pass


def parse_ident(ident, generic=False):
    """

    :type ident: str
    """
    device = None
    value = None
    footprint = None
    for st in DEVICE_CLASSES:
        if ident.startswith(st):
            device = st
            break
    if device is not None:
        ident = ident[len(device):]
    parts = ident.split()
    for st in nofp_strs:
        if device is not None and device.startswith(st):
            footprint = None
            value = ' '.join(parts)
    if generic is True and fpiswire(device):
        footprint = None
        value = ' '.join(parts)
    if value is None:
        try:
            footprint = parts[-1]
        except IndexError:
            raise MalformedIdentError(ident)
        value = ' '.join(parts[:-1])
    # TODO Parse Value for Special Devices?
    # TODO Obtain gEDA symbol for fancier verification?
    # TODO Check Generators?
    return device, value, footprint


jb_component = namedtuple('jb_component',
                          'code typeclass required get_default criteria')


def _jellybean_match(tcomponents, p1, p2):
    score = 0
    for component in tcomponents:
        p1v = getattr(p1, component.code)
        p2v = getattr(p2, component.code)
        if p1v is not None:
            if not isinstance(p1v, component.typeclass):
                p1v = component.typeclass(p1v)
            if p2v is None:
                # TODO Decide how this should be handled.
                return 0
            if not isinstance(p2v, component.typeclass):
                p2v = component.typeclass(p2v)
            if component.criteria == 'EQUAL':
                if p1v != p2v:
                    return 0
                else:
                    score += 2
            elif component.criteria == 'ATLEAST':
                if p1v > p2v:
                    return 0
                elif p1v == p2v:
                    score += 2
                else:
                    score += 1
            elif component.criteria == 'ATMOST':
                if p1v < p2v:
                    return 0
                elif p1v == p2v:
                    score += 2
                else:
                    score += 1
    return score


def _jellybean_bestmatch(tcomponents, target, candidates):
    if len(candidates) == 1:
        return candidates[0][0]
    candidates = [c[0] for c in candidates]
    scores = [0] * len(candidates)
    for idx, candidate in enumerate(candidates):
        for component in tcomponents:
            code = component.code
            if component.criteria == 'EQUAL':
                continue
            if not isinstance(component.typeclass, NumericalUnitBase):
                continue
            elif component.criteria == 'ATLEAST':
                f = getattr(candidate, code) / getattr(target, code)
            elif component.criteria == 'ATMOST':
                f = getattr(target, code) / getattr(component, code)
            else:
                raise Exception
            scores[idx] += f
    candidates = sorted(zip(candidates, scores), key=lambda y: y[1])
    return candidates[0][0]


def _jellybean_packer(ttype, tcomponents, tcontext, **kwargs):
    """
    Pack components for a jellybean part into a structured form. Also applies
    defaults when needed and supported at this stage.
    
    :param ttype: 
    :param tcomponents: 
    :param kwargs: 
    :return: 
    """
    for component in tcomponents:
        v = kwargs.get(component.code, None)
        if v is None:
            if component.required:
                raise ParseException
            elif component.get_default is not None:
                default = component.get_default(tcontext)
                kwargs[component.code] = default
            else:
                kwargs[component.code] = None
        v = kwargs.get(component.code, None)
        if v is not None and not isinstance(v, component.typeclass):
            kwargs[component.code] = component.typeclass(v)

    return ttype(**kwargs)


def _jellybean_parser(ttype, tcomponents, tcontext, value):
    """
    Parses the standard form of the value for a jellybean part. Returns the 
    components in a structured form, constructed by _jellybean_packer where 
    defaults are applied.
    
    :param ttype: 
    :param tcomponents: 
    :param tcontext: 
    :param value: 
    :return: 
    """
    rparts = {}
    sparts = value.split('/')

    while len(sparts):
        part = sparts.pop(0)
        handled = False
        while not handled and len(tcomponents):
            component = tcomponents.pop(0)
            try:
                rparts[component.code] = component.typeclass(part)
                handled = True
            except ParseException as e:
                if component.required:
                    raise e
                else:
                    rparts[component.code] = None

    if len(tcomponents):
        for component in tcomponents:
            if component.required:
                raise ParseException
            else:
                rparts[component.code] = None

    return _jellybean_packer(ttype, tcomponents, tcontext, **rparts)


def _jellybean_constructor(tcomponents, **kwargs):
    """
    Construct a valid value string from components for jellybean parts. The  
    provided structured forms can be provided directly as kwargs.
    
    :param tcomponents: 
    :param kwargs: 
    :return: 
    """
    rparts = []
    for component in tcomponents:
        part = kwargs.pop(component.code)
        if part:
            if issubclass(component.typeclass, NumericalUnitBase):
                cpart = component.typeclass(part)
                # TODO Fix precision issue for Numerical Unit Base
                if cpart != component.typeclass(part):
                    raise ValueError
            elif not isinstance(part, component.typeclass):
                part = component.typeclass(part)
            rparts.append(str(part))
    return '/'.join(rparts)


_r_parts = [jb_component('resistance', Resistance, True, None, 'EQUAL'),
            jb_component('wattage', ThermalDissipation, False, None, 'ATLEAST'),
            jb_component('tolerance', Tolerance, False, None, 'ATMOST'),
            jb_component('tc', str, False, None, 'EQUAL')]

Resistor = namedtuple('Resistor', ' '.join([x[0] for x in _r_parts]))


def jb_resistor_defs():
    return copy(_r_parts)


def jb_resistor(resistance, wattage=None, tolerance=None, tc=None,
                context=None):
    return _jellybean_packer(Resistor, jb_resistor_defs(), tcontext=context,
                             resistance=resistance, wattage=wattage,
                             tolerance=tolerance, tc=tc)


def match_resistor(tresistor, sresistor):
    return _jellybean_match(jb_resistor_defs(), tresistor, sresistor)


def bestmatch_resistor(tresistor, candidates):
    return _jellybean_bestmatch(jb_resistor_defs(), tresistor, candidates)


def parse_resistor(value, context=None):
    return _jellybean_parser(Resistor, jb_resistor_defs(), context, value)


def construct_resistor(resistance, wattage=None, tolerance=None, tc=None):
    return _jellybean_constructor(jb_resistor_defs(),
                                  resistance=resistance, wattage=wattage,
                                  tolerance=tolerance, tc=tc)


_c_parts = [jb_component('capacitance', Capacitance, True, None, 'EQUAL'),
            jb_component('voltage', Voltage, False, None, 'ATLEAST'),
            jb_component('tolerance', Tolerance, False, None, 'ATMOST'),
            jb_component('tcc', str, False, None, 'EQUAL')]

Capacitor = namedtuple('Capacitor', ' '.join([x[0] for x in _c_parts]))


def jb_capacitor_defs():
    return copy(_c_parts)


def jb_capacitor(capacitance,
                 voltage=None, tolerance=None, tcc=None, context=None):
    return _jellybean_packer(Capacitor, jb_capacitor_defs(), tcontext=context,
                             capacitance=capacitance, voltage=voltage,
                             tolerance=tolerance, tcc=tcc)


def match_capacitor(tcapacitor, scapacitor):
    return _jellybean_match(jb_capacitor_defs(), tcapacitor, scapacitor)


def bestmatch_capacitor(tcapacitor, candidates):
    return _jellybean_bestmatch(jb_capacitor_defs(), tcapacitor, candidates)


def parse_capacitor(value, context=None):
    return _jellybean_parser(Capacitor, jb_capacitor_defs(), context, value)


def construct_capacitor(capacitance, voltage=None, tolerance=None, tcc=None):
    return _jellybean_constructor(jb_capacitor_defs(),
                                  capacitance=capacitance, voltage=voltage,
                                  tolerance=tolerance, tcc=tcc)


def parse_inductor(value):
    rex = re.compile(r'^(?P<inductance>\d+(.\d+)*[pnum]H)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['inductance']
    except AttributeError:
        return None


def construct_inductor(inductance):
    value = inductance
    try:
        cinductance = parse_inductor(value)
        if cinductance != inductance:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def parse_crystal(value):
    rex = re.compile(r'^(?P<frequency>\d+(.\d+)*[KM]Hz)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['frequency']
    except AttributeError:
        return None


def construct_crystal(frequency):
    value = frequency
    try:
        cfrequency = parse_crystal(value)
        if cfrequency != frequency:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def parse_led(value):
    rex = re.compile(r'^(?P<color>RED|GREEN|YELLOW|BLUE|WHITE|BICOLOR)(/(?P<voltage>[\d.]+V))?(/(?P<wattage>[\d.]+W))?$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict.get('color', None), \
            rdict.get('voltage', None), \
            rdict.get('wattage', None)
    except AttributeError:
        return None


_std_checkers = [
    ('RES', parse_resistor),
    ('CAP', parse_capacitor),
    ('CRYSTAL', parse_crystal),
    ('LED', parse_led)
]


def check_for_std_val(ident):
    device, value, footprint = parse_ident(ident)
    return check_for_jb_component(device, value, footprint)


def check_for_jb_component(device, value, footprint):
    vals = None
    prefix = None
    for prefix, checker in _std_checkers:
        if not device:
            return False
        if device.startswith(prefix):
            try:
                vals = checker(value)
                break
            except ParseException:
                pass
    if vals is not None:
        return prefix
    return False


def jb_harmonize(item):
    ident = ident_transform(item.data['device'],
                            item.data['value'],
                            item.data['footprint'])
    prefix = check_for_std_val(ident)
    if not prefix:
        return item
    else:
        if item.data['footprint'].startswith('MY-'):
            item.data['footprint'] = item.data['footprint'][3:]
        context = {'device': item.data['device'],
                   'footprint': item.data['footprint']}
        if prefix == 'RES':
            params = parse_resistor(item.data['value'], context)
            from tendril.gedaif.gsymlib import find_resistor
            from tendril.gedaif.gsymlib import NoGedaSymbolException
            try:
                resistor = find_resistor(item.data['device'],
                                         item.data['footprint'],
                                         **params._asdict())
                item.data['value'] = resistor.value
            except NoGedaSymbolException:
                pass
            return item
        elif prefix == 'CAP':
            params = parse_capacitor(item.data['value'], context)
            from tendril.gedaif.gsymlib import find_capacitor
            from tendril.gedaif.gsymlib import NoGedaSymbolException
            try:
                capacitor = find_capacitor(item.data['device'],
                                           item.data['footprint'],
                                           **params._asdict())
                item.data['value'] = capacitor.value
            except NoGedaSymbolException:
                pass
            return item
        else:
            return item
