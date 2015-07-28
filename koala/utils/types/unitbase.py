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
            if 1 <= value < 1000:
                done = True
            elif value >= 1000:
                if ostri < len(self._ostrs) - 1:
                    ostr = self._ostrs[ostri + 1]
                    value /= Decimal(1000)
                else:
                    done = True
            elif value < 1:
                if ostri > 0:
                    ostr = self._ostrs[ostri - 1]
                    value *= Decimal(1000)
                else:
                    done = True
        return str(value) + ostr
