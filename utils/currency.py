"""
Currency module documentation (:mod:`utils.currency`)
=====================================================
"""

from utils.config import BASE_CURRENCY
from utils.config import BASE_CURRENCY_SYMBOL

import utils.www
import urllib
import urllib2
import json


class CurrencyDefinition(object):
    def __init__(self, code, symbol=None, exchval=None):
        self._code = code
        self._symbol = symbol
        if exchval is not None:
            self._exchval = exchval
        else:
            self._exchval = self._get_exchval(self._code)

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
        response = utils.www.urlopen(request)
        data = json.load(response)
        rate = float(data['rate'])
        return rate

native_currency_defn = CurrencyDefinition(BASE_CURRENCY, BASE_CURRENCY_SYMBOL)


class CurrencyValue(object):
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
        return BASE_CURRENCY_SYMBOL + str(self.native_value)

    @property
    def source_value(self):
        return self._val

    @property
    def source_string(self):
        return self._currency_def.symbol + str(self._val)

    @property
    def source_currency(self):
        return self._currency_def

    def __repr__(self):
        return self.native_string

    def __float__(self):
        return self.native_value



