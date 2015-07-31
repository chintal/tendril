# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Koala.
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
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from decimal import Decimal
import numbers


class UnitBase(object):
    def __init__(self, value, _ostrs, _dostr, _parse_func):
        if isinstance(value, str):
            value = _parse_func(value)
        elif isinstance(value, numbers.Number):
            if not isinstance(value, Decimal):
                value = Decimal(value)

        self._value = value
        self._ostrs = _ostrs
        self._dostr = _dostr

    # def __float__(self):
    #     return float(self._value)
    #
    # def __int__(self):
    #     return int(self._value)

    @property
    def value(self):
        return self._value

    def __add__(self, other):
        return self.__class__(self.value + other.value)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            return self.__class__(self.value * other)
        else:
            raise TypeError

    def __div__(self, other):
        if isinstance(other, numbers.Number):
            return self.__class__(self.value / other)
        elif isinstance(other, self.__class__):
            return self.value / other.value
        else:
            raise TypeError

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other.__mul__(-1))

    def __cmp__(self, other):
        if self.value == other.value:
            return 0
        elif self.value < other.value:
            return -1
        else:
            return 1

    def __repr__(self):
        ostr = self._dostr
        value = self._value
        done = False
        while not done:
            ostri = self._ostrs.index(ostr)
            if 1 <= abs(value) < 1000:
                done = True
            elif abs(value) >= 1000:
                if ostri < len(self._ostrs) - 1:
                    ostr = self._ostrs[ostri + 1]
                    value /= Decimal(1000)
                else:
                    done = True
            elif abs(value) < 1:
                if ostri > 0:
                    ostr = self._ostrs[ostri - 1]
                    value *= Decimal(1000)
                else:
                    done = True
        return str(value) + ostr


class DummyUnit(UnitBase):
    def __init__(self, value):
        super(DummyUnit, self).__init__(value, None, None, None)

    def __repr__(self):
        return "Dummy Unit"


def parse_none(value):
    return value


def parse_percent(value):
    value = value.strip()
    if value.endswith('%'):
        return Decimal(value[:-1])
    return Decimal(value)


class Percentage(UnitBase):
    def __init__(self, value):
        _ostrs = ['%']
        _dostr = '%'
        _parse_func = parse_percent
        super(Percentage, self).__init__(value, _ostrs, _dostr, _parse_func)