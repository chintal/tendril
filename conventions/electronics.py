"""
Electronics Conventions Module documentation (:mod:`conventions.electronics`)
=============================================================================
"""

import logging
import re

DEVICE_CLASSES = [
    'RES SMD',
    'RES THRU',
    'RES POWER',
    'RES ARRAY THRU',
    'RES ARRAY SMD',
    'POT TRIM',
    'VARISTOR',
    'CAP CER SMD',
    'CAP TANT SMD',
    'CAP CER THRU',
    'CAP ELEC THRU',
    'CAP POLY THRU',
    'CAP PAPER THRU',
    'INDUCTOR SMD',
    'INDUCTOR THRU',
    'FERRITE BEAD SMD',
    'TRANSFORMER HEAVY',
    'TRANSFORMER SMD',
    'DIODE SMD',
    'DIODE THRU',
    'ZENER SMD',
    'ZENER THRU',
    'TRIAC',
    'LED SMD',
    'LED THRU',
    'LED MODULE',
    'BRIDGE RECTIFIER',
    'CRYSTAL AT',
    'CRYSTAL TF',
    'CRYSTAL OSC',
    'TRANSISTOR THRU',
    'TRANSISTOR SMD',
    'IC THRU',
    'IC DIP',
    'IC SMD',
    'IC PLCC',
    'IC POWER',
    'SOCKET STRIP',
    'SOCKET DIP',
    'RELAY',
    'MODULE',
    'PCB',
    'BUZZER',
    'CONN BANANA',
    'CONN BERG STRIP',
    'CONN TERMINAL BLOCK',
    'CONN TERMINAL',
    'CONN DTYPE',
    'CONN INTERBOARD',
    'CONN FRC',
    'CONN MINIDIN',
    'CONN MOLEX MINIFIT',
    'CONN MOLEX',
    'CONN BARREL',
    'CONN SIP',
    'CONN STEREO',
    'CONN DF13',
    'CONN MODULAR',
    'SWITCH TACT',
    'SWITCH PUSHBUTTON',
    'TESTPOINT',
    'SOLDER DOT',
    'BATTERY'
]

nofp_strs = [
    "CONN",
    "MODULE",
    "CRYSTAL OSC"
]


def ident_transform(device, value, footprint, tf=None):
    """
    Auto-generated ident string from the component ``device``, ``value``
    and ``footprint`` attributes.

    If the device string starts with any of the strings in ``nofp_strings``,
    the ``footprint`` is excluded from the ``ident`` string.

    When applied to gEDA generated data (BOMs, gsymlib), the return value is
    the ``Canonical Representation`` for the component. The burden of ensuring
    uniqueness and consistency is on the gEDA schematic files and authors
    thereof. See conventions.rst listed in ``somewhere`` for relevant guidelines.

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
        logging.error('Error generating ident : ' + str(device) + ' ' + str(value) + ' ' + str(footprint))
        ident = 'FATAL'
    for st in nofp_strs:
        if device.startswith(st):
            ident = device + " " + value
    if tf is None:
        return ident
    else:
        return tf.get_canonical(tf)


def parse_ident(ident):
    """

    :type ident: str
    """
    device = None
    value = None
    footprint = None
    for st in DEVICE_CLASSES:
        if ident.startswith(st):
            device = st
    if device is not None:
        ident = ident[len(device):]
    parts = ident.split()
    for st in nofp_strs:
        if device is not None and device.startswith(st):
            footprint = None
            value = ' '.join(parts)
    if value is None:
        footprint = parts[-1]
        value = ' '.join(parts[:-1])
    # TODO Parse Value for Special Devices?
    # TODO Obtain gEDA symbol for fancier verification?
    # TODO Check Generators?
    return device, value, footprint


def construct_resistor(resistance, wattage):
    value = '/'.join([resistance, wattage])
    try:
        cresistance, cwattage = parse_resistor(value)
        if cresistance != resistance:
            raise ValueError
        if cwattage != wattage:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_capacitor(capacitance, voltage):
    value = '/'.join([capacitance, voltage])
    try:
        ccapacitance, cvoltage = parse_capacitor(value)
        if ccapacitance != capacitance:
            raise ValueError
        if cvoltage != voltage:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_inductor(inductance):
    value = inductance
    try:
        cinductance = parse_inductor(value)
        if cinductance != inductance:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def construct_crystal(frequency):
    value = frequency
    try:
        cfrequency = parse_crystal(value)
        if cfrequency != frequency:
            raise ValueError
    except AttributeError:
        raise ValueError
    return value


def parse_resistor(value):
    rex = re.compile(r'^(?P<resistance>\d+(.\d+)*[mEKM])(/(?P<wattage>\d+(.\d+)*W))*$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['resistance'], rdict['wattage']
    except AttributeError:
        return None


def parse_capacitor(value):
    rex = re.compile(r'^(?P<capacitance>\d+(.\d+)*[pnum]F)(/(?P<voltage>\d+(.\d+)*V(DC|AC)*))*$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['capacitance'], rdict['voltage']
    except AttributeError:
        return None


def parse_inductor(value):
    rex = re.compile(r'^(?P<inductance>\d+(.\d+)*[pnum]H)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['inductance']
    except AttributeError:
        return None


def parse_crystal(value):
    rex = re.compile(r'^(?P<frequency>\d+(.\d+)*[KM]Hz)$')
    try:
        rdict = rex.search(value).groupdict()
        return rdict['frequency']
    except AttributeError:
        return None

