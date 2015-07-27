"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from decimal import Decimal
from decimal import InvalidOperation
import numbers

from unitbase import UnitBase


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


class Voltage(UnitBase):
    def __init__(self, value):
        if isinstance(value, str):
            value = parse_voltage(value)
        elif isinstance(value, numbers.Number):
            value = Decimal(value)
        super(Voltage, self).__init__(value)

    def __repr__(self):
        if self._value >= 1000:
            return str(self._value / 1000) + 'kV'
        elif self._value >= 1:
            return str(self._value) + 'V'
        elif self._value >= 0.001:
            return str(self._value * 1000) + 'mV'
        elif self._value >= 0.000001:
            return str(self._value * 1000000) + 'uV'
        elif self._value >= 0.000000001:
            return str(self._value * 1000000000) + 'nV'
        else:
            return str(self._value * 1000000000000) + 'pV'


class Current(UnitBase):
    def __init__(self, value):
        if isinstance(value, str):
            value = parse_current(value)
        elif isinstance(value, numbers.Number):
            value = Decimal(value)
        super(Current, self).__init__(value)

    def __repr__(self):
        if self._value > 1000:
            return str(self._value / 1000) + 'A'
        elif self._value > 1:
            return str(self._value) + 'mA'
        elif self._value > 0.001:
            return str(self._value * 1000) + 'uA'
        elif self._value > 0.000001:
            return str(self._value * 1000000) + 'nA'
        elif self._value > 0.000000001:
            return str(self._value * 1000000000) + 'pA'
        else:
            return str(self._value * 1000000000000) + 'fA'
