"""
Vendors module documentation (:mod:`sourcing.vendors`)
======================================================
"""

import entityhub.maps
import utils.currency


class Vendor(object):
    def __init__(self, name, dname, mapfile, pclass):
        self._name = name
        self._map = entityhub.maps.MapFile(mapfile)
        self._dname = dname
        self._currency = None
        self._pclass = pclass

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, code, symbol=None):
        self._currency = utils.currency.CurrencyDefinition(code, symbol)


class VendorPrice(object):
    def __init__(self, moq, price, currency_def):
        self._moq = moq
        self._price = utils.currency.CurrencyValue(price, currency_def)

    @property
    def moq(self):
        return self._moq

    @property
    def native_value(self):
        return self._price.native_value


class VendorPart(object):
    def __init__(self):
        self._manufacturer = None
        self._mpartno = None
        self._canonical_repr = None
        self._prices = []


class VendorElnPart(VendorPart):
    def __init__(self):
        super(VendorElnPart, self).__init__()
        self._package = None
        self._datasheet = None

