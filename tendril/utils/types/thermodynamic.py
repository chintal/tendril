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


from decimal import Decimal
from decimal import InvalidOperation
from .unitbase import NumericalUnitBase


def parse_temperature(value):
    num_val = Decimal(value[:-1].strip())
    ostr = value[-1:]
    if ostr == 'C':
        return num_val + Decimal('273.14')
    elif ostr == 'K':
        return num_val
    elif ostr == 'F':
        return ((num_val - 32) * 5) / 9 + Decimal('273.14')


class Temperature(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['C', 'F', 'K']
        _dostr = 'K'
        _parse_func = parse_temperature
        super(Temperature, self).__init__(value, _ostrs, _dostr, _parse_func)

    def __repr__(self):
        return str(self._value) + self._dostr


def parse_power(value):
    value = value.strip()

    try:
        num_val = Decimal(value[:-1])
        ostr = value[-1:]
    except InvalidOperation:
        num_val = Decimal(value[:-2])
        ostr = value[-2:]

    if ostr == 'W':
        return num_val
    elif ostr == 'mW':
        return num_val / 1000
    elif ostr == 'uW':
        return num_val / 1000000
    elif ostr == 'nW':
        return num_val / 1000000000
    elif ostr == 'kW':
        return num_val * 1000
    elif ostr == 'MW':
        return num_val * 1000
    else:
        raise ValueError


class ThermalDissipation(NumericalUnitBase):
    def __init__(self, value):
        _ostrs = ['nW', 'uW', 'mW', 'W', 'kW', 'MW']
        _dostr = 'W'
        _parse_func = parse_power
        super(ThermalDissipation, self).__init__(value, _ostrs, _dostr, _parse_func)
