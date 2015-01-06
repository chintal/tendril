"""
Electronics Conventions Module documentation (:mod:`boms.electronics`)
======================================================================
"""

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

    ident = device + " " + value + " " + footprint
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
    ident = ident[len(device):]
    parts = ident.split()
    for st in nofp_strs:
        if device.startswith(st):
            footprint = None
            value = ' '.join(parts)
    if value is None:
        footprint = parts[-1]
        value = ' '.join(parts[:-1])
    # TODO Parse Value for Special Devices?
    # TODO Obtain gEDA symbol for fancier verification?
    # TODO Check Generators?
    return device, value, footprint
