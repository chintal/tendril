"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from decimal import Decimal
from decimal import InvalidOperation

from unitbase import UnitBase


def parse_resistance(value):
    num_val = Decimal(value[:-1])
    ostr = value[-1:]
    if ostr == 'm':
        return num_val / 1000
    elif ostr == 'E':
        return num_val
    elif ostr == 'K':
        return num_val * 1000
    elif ostr == 'M':
        return num_val * 1000 * 1000


def parse_capacitance(value):
    num_val = Decimal(value[:-2])
    ostr = value[-2:]
    if ostr == 'pF':
        return num_val / 1000
    elif ostr == 'nF':
        return num_val
    elif ostr == 'uF':
        return num_val * 1000
    elif ostr == 'mF':
        return num_val * 1000 * 1000


def parse_voltage(value):
    value = value.strip()
    try:
        num_val = Decimal(value[:-1])
        ostr = value[-1:]
    except InvalidOperation:
        num_val = Decimal(value[:-2])
        ostr = value[-2:]

    if ostr == 'V':
        return num_val
    elif ostr == 'mV':
        return num_val / 1000
    elif ostr == 'uV':
        return num_val / 1000000
    elif ostr == 'nV':
        return num_val / 1000000000
    elif ostr == 'pV':
        return num_val / 1000000000000
    elif ostr == 'kV':
        return num_val * 1000
    else:
        raise ValueError


def parse_current(value):
    value = value.strip()
    try:
        num_val = Decimal(value[:-1])
        ostr = value[-1:]
    except InvalidOperation:
        num_val = Decimal(value[:-2])
        ostr = value[-2:]

    if ostr == 'A':
        return num_val * 1000
    elif ostr == 'mA':
        return num_val
    elif ostr == 'uA':
        return num_val / 1000
    elif ostr == 'nA':
        return num_val / 1000000
    elif ostr == 'pA':
        return num_val / 1000000000
    elif ostr == 'fA':
        return num_val / 1000000000000
    else:
        raise ValueError


class Resistance(UnitBase):
    def __init__(self, value):
        _ostrs = ['m', 'E', 'K', 'M']
        _dostr = 'E'
        _parse_func = parse_resistance
        super(Resistance, self).__init__(value, _ostrs, _dostr, _parse_func)


class Capacitance(UnitBase):
    def __init__(self, value):
        _ostrs = ['pF', 'nF', 'uF', 'mF']
        _dostr = 'nF'
        _parse_func = parse_capacitance
        super(Capacitance, self).__init__(value, _ostrs, _dostr, _parse_func)


class Voltage(UnitBase):
    def __init__(self, value):
        _ostrs = ['pV', 'nV', 'uV', 'mV', 'V', 'kV']
        _dostr = 'V'
        _parse_func = parse_voltage
        super(Voltage, self).__init__(value, _ostrs, _dostr, _parse_func)


class Current(UnitBase):
    def __init__(self, value):
        _ostrs = ['fA', 'pA', 'nA', 'uA', 'mA', 'A']
        _dostr = 'mA'
        _parse_func = parse_current
        super(Current, self).__init__(value, _ostrs, _dostr, _parse_func)
