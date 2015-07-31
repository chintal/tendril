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
Currency Types (:mod:`koala.utils.types.currency`)
==================================================

The :mod:`koala.utils.types.currency` contains classes which allow for easy
use and manipulation of currency values. The primary focus is on the primary
use cases of Currencies within koala, i.e. :

- Handling foreign exchange conversions and exchange rates in application code
  without too much fuss.
- Handling currency arithmetic and comparisons.

This module uses a specific `Base Currency`, defined by :const:`koala.utils.config.BASE_CURRENCY`
and :const:`koala.utils.config.BASE_CURRENCY_SYMBOL` and available as this
module's :data:`native_currency_defn` module variable. In case this module is
to be used independent of Koala, at least those configuration options *must* be
defined in :mod:`koala.utils.config`.

.. rubric:: Module Contents

.. autosummary::

    native_currency_defn
    CurrencyDefinition
    CurrencyValue

.. seealso:: :mod:`koala.utils.types`, for an overview applicable to most types defined in Koala.

"""

from koala.utils.config import BASE_CURRENCY
from koala.utils.config import BASE_CURRENCY_SYMBOL

from koala.utils import www
import urllib
import urllib2
import json
import numbers


class CurrencyDefinition(object):
    """
    Test
    """
    def __init__(self, code, symbol=None, exchval=None):
        self._code = code
        self._symbol = symbol
        if exchval is not None:
            self._exchval = exchval
        else:
            self._exchval = self._get_exchval(self._code)

    @property
    def code(self):
        return self._code

    @property
    def symbol(self):
        if self._symbol is not None:
            return self._symbol
        else:
            return self._code

    @property
    def exchval(self):
        return self._exchval

    @staticmethod
    def _get_exchval(code):
        apiurl = 'http://jsonrates.com/get/?'
        params = {'from': code,
                  'to': BASE_CURRENCY,
                  'apiKey': 'jr-b612b56a860a1e7e6de8863d3379404f'}
        request = urllib2.Request(apiurl + urllib.urlencode(params))
        response = www.urlopen(request)
        data = json.load(response)
        try:
            rate = float(data['rate'])
        except KeyError:
            raise KeyError(code)
        return rate

    def __eq__(self, other):
        if self.code != other.code:
            return False
        if self.symbol != other.symbol:
            return False
        if self.exchval != other.exchval:
            return False
        return True

#: The native currency definition used by the module
#:
#: This definition uses the code contained in
#: :const:`koala.utils.config.BASE_CURRENCY` and symbol
#: :const:`koala.utils.config.BASE_CURRENCY_SYMBOL`. Application
#: code should import this definition instead of creating new currency
#: definitions whenever one is needed to represent a native currency value.
native_currency_defn = CurrencyDefinition(BASE_CURRENCY, BASE_CURRENCY_SYMBOL)


class CurrencyValue(object):
    """
    Test
    """
    def __init__(self, val, currency_def):
        if isinstance(currency_def, CurrencyDefinition):
            self._currency_def = currency_def
        else:
            self._currency_def = CurrencyDefinition(currency_def)
        self._val = val

    @property
    def native_value(self):
        return self._val * self._currency_def.exchval

    @property
    def native_string(self):
        return BASE_CURRENCY_SYMBOL + "{0:,.2f}".format(self.native_value)

    @property
    def source_value(self):
        return self._val

    @property
    def source_string(self):
        return self._currency_def.symbol + "{0:,.2f}".format(self._val)

    @property
    def source_currency(self):
        return self._currency_def

    def __repr__(self):
        return self.native_string

    def __float__(self):
        return self.native_value

    def __add__(self, other):
        if self._currency_def.symbol == other.source_currency.symbol:
            return CurrencyValue(self.source_value + other.source_value, self.source_currency)
        else:
            return CurrencyValue(self.native_value + other.native_value, native_currency_defn)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            return CurrencyValue(self.source_value * other, self.source_currency)
        else:
            raise TypeError

    def __div__(self, other):
        if isinstance(other, numbers.Number):
            return CurrencyValue(self.source_value / other, self.source_currency)
        elif isinstance(other, CurrencyValue):
            return self.native_value / other.native_value
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
        if not isinstance(other, CurrencyValue):
            raise TypeError
        if self.native_value == other.native_value:
            return 0
        elif self.native_value < other.native_value:
            return -1
        else:
            return 1
