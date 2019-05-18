#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for costingbase
"""

from tendril.gedaif.gsymlib import get_symbol
from tendril.libraries.edasymbols import nosymbolexception
from tendril.inventory.guidelines import electronics_qty

from tendril.utils.types.currency import CurrencyValue
from tendril.utils.types.currency import native_currency_defn

from tendril.validation.base import ErrorCollector

from tendril.costing.breakup import OBomCostingBreakup
from tendril.validation.sourcing import SourcingIdentNotRecognized
from tendril.validation.sourcing import SourcingIdentNotSourceable


class NoStructureHereException(Exception):
    pass


class SourceableBomLineMixin(object):
    def __init__(self):
        self._isinfo = ''
        self._sourcing_exception = None

    @property
    def ident(self):
        raise NotImplementedError

    @ident.setter
    def ident(self, value):
        raise NotImplementedError

    @property
    def parent(self):
        raise NotImplementedError

    @parent.setter
    def parent(self, value):
        raise NotImplementedError

    @property
    def refdeslist(self):
        raise NotImplementedError

    @refdeslist.setter
    def refdeslist(self, value):
        raise NotImplementedError

    @property
    def quantity(self):
        raise NotImplementedError

    @property
    def uquantity(self):
        raise NotImplementedError

    def _get_isinfo(self):
        # qty = electronics_qty.get_compliant_qty(self.ident, self.quantity)
        if self.ident.startswith('PCB'):
            from tendril.entityhub.modules import get_pcb_lib
            pcblib = get_pcb_lib()
            ident = self.ident[len('PCB '):]
            if ident in pcblib.keys():
                symbol = pcblib[ident]
            else:
                self._isinfo = None
                self._sourcing_exception = SourcingIdentNotRecognized(
                    self.parent.sourcing_policy, self.ident, self.refdeslist
                )
                return
        else:
            try:
                symbol = get_symbol(self.ident)
            except nosymbolexception:
                self._isinfo = None
                self._sourcing_exception = SourcingIdentNotRecognized(
                    self.parent.sourcing_policy, self.ident, self.refdeslist
                )
                return
        try:
            self._isinfo = symbol.indicative_sourcing_info[0]
        except IndexError:
            self._isinfo = None
            self._sourcing_exception = SourcingIdentNotSourceable(
                self.parent.sourcing_policy, self.ident, self.refdeslist
            )

    @property
    def isinfo(self):
        if self._isinfo == '':
            self._get_isinfo()
        return self._isinfo

    @property
    def sourcing_error(self):
        if self._isinfo == '':
            self._get_isinfo()
        return self._sourcing_exception

    @property
    def indicative_cost(self):
        if self.isinfo is not None:
            qty = electronics_qty.get_compliant_qty(self.ident, self.quantity)
            ubprice, nbprice = self.isinfo.vpart.get_price(qty)
            if ubprice is not None:
                price = ubprice
            elif nbprice is not None:
                price = nbprice
            else:
                price = self.isinfo.ubprice
            effprice = self.isinfo.vpart.get_effective_price(price)
            return effprice.extended_price(self.uquantity, allow_partial=True)
        else:
            return None


class CostableBom(object):
    def __init__(self):
        self._lines = []

        self._sourcing_errors = None
        self._indicative_cost = None
        self._indicative_cost_breakup = None

    @property
    def ident(self):
        raise NotImplementedError

    @property
    def lines(self):
        return self._lines

    @property
    def indicative_cost(self):
        if self._indicative_cost is None:
            self._indicative_cost = CurrencyValue(0, native_currency_defn)
            for line in self.lines:
                lcost = line.indicative_cost
                if lcost is not None:
                    self._indicative_cost += lcost
        return self._indicative_cost

    def _build_indicative_cost_breakup(self):
        self._indicative_cost_breakup = \
            OBomCostingBreakup(self.ident)
        for line in self.lines:
            lcost = line.indicative_cost
            if lcost is not None:
                self._indicative_cost_breakup.insert(line.ident, lcost)
        self._indicative_cost_breakup.sort()

    @property
    def indicative_cost_breakup(self):
        if self._indicative_cost_breakup is None:
            self._build_indicative_cost_breakup()
        return self._indicative_cost_breakup

    @property
    def sourcing_errors(self):
        if self._sourcing_errors is None:
            self._sourcing_errors = ErrorCollector()
            for line in self.lines:
                if line.sourcing_error is not None:
                    self._sourcing_errors.add(line.sourcing_error)
        return self._sourcing_errors
