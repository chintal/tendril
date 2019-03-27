#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016-2019 Chintalagiri Shashank
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


import json

from future.utils import viewitems

from tendril.conventions.electronics import parse_ident
from tendril.utils.types.currency import native_currency_defn
from tendril.utils.types.currency import CurrencyValue


class CostingBreakupBase(object):
    def __init__(self, name):
        self._name = name
        self._currency_symbol = native_currency_defn.symbol

    @property
    def name(self):
        return self._name

    @property
    def currency_symbol(self):
        return self._currency_symbol

    @property
    def total_cost(self):
        raise NotImplementedError

    @property
    def sections(self):
        raise NotImplementedError

    @property
    def content(self):
        return [{'name': k, 'children': v} for k, v in self._content]

    @property
    def _content(self):
        raise NotImplementedError

    @property
    def json(self):
        return json.dumps(
            {'name': self._name,
             'children': self.content
             }
        )


class OBomCostingBreakup(CostingBreakupBase):
    def __init__(self, name):
        super(OBomCostingBreakup, self).__init__(name)
        self._devices = {}
        self._total_cost = CurrencyValue(0, native_currency_defn)

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
    def _content(self):
        return sorted(viewitems(self._devices),
                      key=lambda x: sum(y['size'] for y in x[1]),
                      reverse=True)


class HierachicalCostingBreakup(CostingBreakupBase):
    def __init__(self, name):
        super(HierachicalCostingBreakup, self).__init__(name)
        self._sections = {}
        self._counters = {}

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
    def _content(self):
        return sorted(viewitems(self._sections),
                      key=lambda x: x[1].total_cost,
                      reverse=True)
