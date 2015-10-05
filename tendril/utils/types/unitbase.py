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
Base Unit Types (:mod:`tendril.utils.types.unitbase`)
=====================================================

The Types provided in this module are not intended for direct use. Instead,
they provide reusable primitives which can be sub-classed to provide
functional Types.

Ideally, all Unit classes should derive from the :class:`UnitBase` class
provided here. In practice, only the newer Types follow this inheritance,
while the older ones still need to be migrated to this form.

.. rubric:: Module Contents

.. autosummary::

    UnitBase
    NumericalUnitBase
    DummyUnit
    parse_none
    parse_percent
    Percentage

.. seealso:: :mod:`tendril.utils.types`, for an overview applicable to
             most types defined in Tendril.

"""

from math import log10
from math import floor
from decimal import Decimal
import six
import numbers


def round_to_n(x, n):
    if x:
        return round(x, -int(floor(log10(x))) + (n - 1))
    return 0


class TypedComparisonMixin(object):
    """
    This mixin allows implementing comparison operators in a Python 3
    compatible way.

    Two instances of a class are compared using their :func:`_cmpkey`
    methods. If the instances have a different ``__class__``, the
    comparison is not implemented. A single exception is implemented,
    for when the other instance is of a numerical type, with value 0.
    """
    def _compare(self, other, method):
        if self.__class__ != other.__class__:
            if not isinstance(other, numbers.Number) or other != 0:
                raise TypeError(
                    "Comparison of : " + repr(self) + ", " + repr(other)
                )
            else:
                return method(self._cmpkey(), other)
        return method(self._cmpkey(), other._cmpkey())

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

    def _cmpkey(self):
        raise NotImplementedError


class UnitBase(object):
    """
    The base class for all :mod:`tendril.utils.types` units.

    When instantiated, the `value` param is processed as follows :

    - :class:`str` value is passed though `_parse_func`, and whatever it
      returns is stored.
    - :class:`numbers.Number` values are first converted into
      :class:`decimal.Decimal` and then stored.
    - All other `value` types are simply stored as is.

    :param value: The core value to be stored.
    :param _dostr: The canonical unit / order string to use.
    :param _parse_func: The function used to parse string values into an
                        actual value in the canonical unit.

    .. rubric:: Arithmetic Operations

    This class supports no arithmetic operations.

    """
    def __init__(self, value, _dostr, _parse_func):
        if isinstance(value, (six.text_type, six.string_types)):
            value = _parse_func(value)
        elif isinstance(value, numbers.Number):
            if not isinstance(value, Decimal):
                value = Decimal(value)

        self._value = value
        self._dostr = _dostr

    # def __float__(self):
    #     return float(self._value)
    #
    # def __int__(self):
    #     return int(self._value)

    @property
    def value(self):
        """
        :return: The core value of the Unit instance, in it's canonical unit.
        """
        return self._value

    def __add__(self, other):
        raise NotImplementedError

    def __radd__(self, other):
        raise NotImplementedError

    def __mul__(self, other):
        raise NotImplementedError

    def __div__(self, other):
        raise NotImplementedError

    def __rmul__(self, other):
        raise NotImplementedError

    def __sub__(self, other):
        raise NotImplementedError

    def _cmpkey(self):
        raise NotImplementedError

    def __repr__(self):
        return str(self._value) + self._dostr


class NumericalUnitBase(TypedComparisonMixin, UnitBase):
    """
    The base class for all :mod:`tendril.utils.types` numerical units.

    Provides the patterns used by the various Numerical Units to provide
    their functionality. This class represents and implements the core
    ideas that remain valid across Units (for the most part). The various
    methods and functions implemented here establish the minimum required
    functionality and behaviour expected of all numerical units.

    Specific numerical unit classes may override the methods present here
    to tweak the implementation and/or the interface as per the
    requirements of the quantity they represent, as long as they stay true
    to the spirit of the architecture.

    :param value: The core value to be stored.
    :param _orders: The recognized orders / units for the Unit.
    :param _dostr: The canonical unit / order string to use.
    :param _parse_func: The function used to parse string values into an
                        actual value in the canonical unit.

    .. seealso:: :class:`UnitBase`

    .. rubric:: The `orders` Parameter

    The `orders` parameter can either be a list of strings or a
    list of tuples.

    - In case it is a `list` of `str`, it is assumed that each string
      represents a unit value 1000 times smaller than the next.
    - In case it is a `list` of `tuple`, it is assumed that the first
      element of the tuple is the string representation of the order,
      and the second element is the multipicative factor relative to
      the default order string.
    - In both cases, note that first order within which the unit value's
      representation lies between 1 and 1000 is used to produce the unit's
      string representation. As such, you should place higher priority or
      more 'standard' units towards the beginning of the list.

    .. rubric:: Arithmetic Operations

    .. autosummary::

        __add__
        __sub__
        __mul__
        __div__
        __cmpkey

    """
    def __init__(self, value, _orders, _dostr, _parse_func):
        super(NumericalUnitBase, self).__init__(value, _dostr, _parse_func)
        if _orders is not None and isinstance(_orders, list):
            if isinstance(_orders[0], str):
                doidx = _orders.index(_dostr)
                self._orders = [(ostr, Decimal(str(10 ** (3 * idx - doidx))))
                                for idx, ostr in enumerate(_orders)]
                self._ostrs = _orders
            if isinstance(_orders[0], tuple):
                self._orders = _orders
                self._ostrs = [order[0] for order in _orders]

    def __float__(self):
        return float(self._value)

    def __add__(self, other):
        """
        Addition of two Unit class instances of the same type returns a
        Unit class instance of the same type, with the sum of the two
        operands as it's value.

        If the other operand is a numerical type and evaluates to 0, this
        object is simply returned unchanged.

        Addition with all other Types / Classes is not supported.
        """
        if isinstance(other, numbers.Number) and other == 0:
            return self
        elif self.__class__ == other.__class__:
            return self.__class__(self.value + other.value)
        else:
            raise NotImplementedError(
                "Addition of : " + repr(self) + " + " + repr(other)
            )

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other):
        """
        Multiplication of one Unit type class instance with a numerical type
        results in a Unit type class instance of the same type, whose value
        is the Unit type operand's value multiplied by the numerical operand's
        value.

        Multiplication with all other Types / Classes is not supported.
        """
        if isinstance(other, numbers.Number):
            if isinstance(self, Percentage):
                return other * self.value / 100
            if isinstance(self, GainBase):
                return self.__class__(other * self.value)
            return self.__class__(other * self.value)
        if isinstance(other, Percentage):
            return self.__class__(self.value * other.value / 100)
        if isinstance(other, GainBase):
            if isinstance(self, GainBase):
                if self._gtype != other._gtype:
                    raise TypeError("Gain is of a different type.")
                return self.__class__(self.value * other.value)
            if other._gtype and not isinstance(self, other._gtype):
                raise TypeError("Gain is of a different type.")
            return self.__class__(self.value * other.value)
        else:
            raise NotImplementedError(
                "Multiplication of : " + repr(self) + " x " + repr(other)
            )

    def __div__(self, other):
        """
        Division of one Unit type class instance with a numerical type
        results in a Unit type class instance of the same type, whose value
        is the Unit type operand's value divided by the numerical operand's
        value.

        In this case, the first operand must be a Unit type class instance,
        and not the reverse.

        Division of one Unit type class instance by another of the same type
        returns a numerical value, which is obtained by performing the
        division with the operands' value.

        Division with all other Types / Classes is not supported.
        """
        if isinstance(other, numbers.Number):
            if isinstance(other, Decimal):
                return self.__class__(self.value / other)
            else:
                return self.__class__(self.value / Decimal(other))
        elif isinstance(other, self.__class__):
            return self.value / other.value
        else:
            raise NotImplementedError(
                "Division of : " + repr(self) + " / " + repr(other)
            )

    def __rdiv__(self, other):
        raise NotImplementedError

    def __truediv__(self, other):
        return self.__div__(other)

    def __rtruediv__(self, other):
        return self.__rdiv__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        """
        Subtraction of two Unit class instances of the same type returns a
        Unit class instance of the same type, with the difference of the two
        operands as it's value.

        If the other operand is a numerical type and evaluates to 0, this
        object is simply returned unchanged.

        Subtraction with all other Types / Classes is not supported.
        """
        if isinstance(other, numbers.Number) and other == 0:
            return self
        else:
            return self.__add__(other.__mul__(-1))

    def __rsub__(self, other):
        return other.__sub__(self)

    def __abs__(self):
        if self._value < 0:
            return self.__class__(self._value * -1)
        else:
            return self

    def _cmpkey(self):
        """
        The comparison of two Unit type class instances of the
        same type behaves identically to the comparison of the
        operands' values.

        Comparison with all other Types / Classes is not supported.
        """
        return self._value

    @property
    def natural_repr(self):
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
        return value, ostr

    @property
    def quantized_repr(self):
        num, unit = self.natural_repr

        neg = False
        if num < 0:
            neg = True
        num = str(round_to_n(float(abs(num)), 5))
        if neg is True:
            num = '-' + num

        return num + unit

    @property
    def integral_repr(self):
        num, unit = self.natural_repr

        neg = False
        if num < 0:
            neg = True
        if num == 0:
            return str(num) + unit
        num = str(round_to_n(float(abs(num)), 2))
        if neg is True:
            num = '-' + num
        return num + unit

    def __repr__(self):
        num, unit = self.natural_repr
        return str(num) + unit


class DummyUnit(UnitBase):
    """
    This class provides a type for placeholder objects. The original
    use case is for handling wave boundaries in streaming protocols.

    Does not support any arithmetic operations.
    """
    def __init__(self, value=None):
        super(DummyUnit, self).__init__(value, None, None)

    def __add__(self, other):
        raise NotImplementedError

    def __radd__(self, other):
        raise NotImplementedError

    def __mul__(self, other):
        raise NotImplementedError

    def __div__(self, other):
        raise NotImplementedError

    def __rmul__(self, other):
        raise NotImplementedError

    def __sub__(self, other):
        raise NotImplementedError

    def __cmp__(self, other):
        raise NotImplementedError

    def __repr__(self):
        return "Dummy Unit"


def parse_none(value):
    """
    A placeholder parse function which can be used if the Unit
    requires / supports no parsing.
    """
    return value


def parse_percent(value):
    """
    A parse function for use by the :class:`Percentage` Type and its
    subclasses.
    """
    value = value.strip()
    if value.endswith('%'):
        return Decimal(value[:-1])
    if value.endswith('pc'):
        return Decimal(value[:-2])
    return Decimal(value)


class Percentage(NumericalUnitBase):
    """
    A base Unit class which provides support for Types that are essentially
    percentages.

    The contribution this base class makes is to be able to parse percentage
    strings so that the Descendant class need not.

    Only the standard :class:`NumericalUnitBase` Arithmetic is supported by
    this class at this time.
    """
    def __init__(self, value):
        _ostrs = ['%']
        _dostr = '%'
        _parse_func = parse_percent
        super(Percentage, self).__init__(value, _ostrs, _dostr, _parse_func)


class GainBase(NumericalUnitBase):
    def __init__(self, value, _orders, _dostr, _parse_func, gtype=None):
        super(GainBase, self).__init__(value, _orders, _dostr, _parse_func)
        self._gtype = gtype

    def in_db(self):
        return 20 * log10(self._value)
