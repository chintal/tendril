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
import json

from future.utils import viewitems

from tendril.conventions.electronics import parse_ident
from tendril.gedaif.gsymlib import get_symbol
from tendril.gedaif.gsymlib import NoGedaSymbolException
from tendril.inventory.guidelines import electronics_qty

from tendril.utils.types.currency import CurrencyValue
from tendril.utils.types.currency import native_currency_defn

from .validate import ErrorCollector
from .validate import ValidationPolicy
from .validate import IdentErrorBase


class SourcingIdentPolicy(ValidationPolicy):
    def __init__(self, context):
        super(SourcingIdentPolicy, self).__init__(context)
        self.is_error = True


class SourcingIdentNotRecognized(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotRecognized, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotRecognized {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' is not a recognized component."
                        "".format(self.ident),
            'detail': "This component is not recognized by the library and "
                      "is therefore not sourceable. Component not included "
                      "in costing analysis. Used by refdes {0}"
                      "".format(', '.join(self.refdeslist)),
        }


class SourcingIdentNotSourceable(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotSourceable, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotSourceable {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}'".format(self.ident),
            'detail': "Viable sources for this component are not known. "
                      "Component not included in costing analysis. Used by "
                      "refdes {0}".format(', '.join(self.refdeslist)),
            'detail_core': ', '.join(self.refdeslist)
        }


class OBomCostingBreakup(object):
    def __init__(self, name):
        self._name = name
        self._currency_symbol = native_currency_defn.symbol
        self._devices = {}
        self._total_cost = CurrencyValue(0, native_currency_defn)

    @property
    def name(self):
        return self._name

    def insert(self, ident, cost):
        d, v, f = parse_ident(ident)
        if d not in self._devices.keys():
            self._devices[d] = []
        self._devices[d].append(
            {'name': ident,
             'size': cost.native_value}
        )
        self._total_cost += cost

    def sort(self):
        for d in self._devices.keys():
            self._devices[d].sort(key=lambda x: x['size'], reverse=True)

    @property
    def sections(self):
        return None

    @property
    def total_cost(self):
        return self._total_cost

    @property
    def currency_symbol(self):
        return self._currency_symbol

    @property
    def content(self):
        return [{'name': k, 'children': v} for k, v in
                sorted(viewitems(self._devices),
                       key=lambda x: sum(y['size'] for y in x[1]),
                       reverse=True)
                ]

    @property
    def json(self):
        return json.dumps(
            {'name': self._name,
             'children': self.content
             }
        )


class HierachicalCostingBreakup(object):
    def __init__(self, name):
        self._name = name
        self._currency_symbol = native_currency_defn.symbol
        self._sections = {}
        self._counters = {}

    @property
    def name(self):
        return self._name

    @property
    def sections(self):
        seclist = [
            (k, int((v.total_cost / self.total_cost) * 100), v.total_cost)
            for k, v in viewitems(self._sections)
        ]
        return sorted(seclist, key=lambda x: x[1], reverse=True)

    @property
    def total_cost(self):
        return sum([v.total_cost for k, v in viewitems(self._sections)])

    def insert(self, ident, breakup):
        if ident not in self._sections.keys():
            self._sections[ident] = breakup
        else:
            if ident in self._counters.keys():
                self._counters[ident] += 1
            else:
                self._counters[ident] = 2
                newname = '.'.join([ident, '1'])
                self._sections[newname] = self._sections.pop(ident)
            newname = '.'.join([ident, str(self._counters[ident])])
            self._sections[newname] = breakup

    @property
    def currency_symbol(self):
        return self._currency_symbol

    @property
    def content(self):
        return [{'name': k, 'children': v.content} for k, v in
                sorted(viewitems(self._sections),
                       key=lambda x: x[1].total_cost,
                       reverse=True)]

    @property
    def json(self):
        return json.dumps(
            {'name': self._name,
             'children': self.content
             }
        )


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
            except NoGedaSymbolException:
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
