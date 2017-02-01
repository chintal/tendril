#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for series.py
"""


import copy
import iec60063
from math import log10

from decimal import InvalidOperation
from tendril.conventions import electronics

from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import Capacitance


class ValueSeries(object):
    def __init__(self, stype, start, end, device, footprint):
        self._stype = stype
        self._start = start
        self._end = end
        self._device = device
        self._footprint = footprint
        if self._stype == 'resistor':
            self._typeclass = Resistance
        if self._stype == 'capacitor':
            self._typeclass = Capacitance

    def gen_vals(self, stype=None, start=None, end=None):
        raise NotImplementedError

    def get_symbol(self, value, device=None, footprint=None):
        from tendril.gedaif import gsymlib

        if device is None:
            device = self._device
        if footprint is None:
            footprint = self._footprint

        if self._stype == 'resistor':
            if isinstance(value, (str, Resistance)):
                try:
                    return gsymlib.find_resistor(value, footprint, device)
                except (gsymlib.NoGedaSymbolException, InvalidOperation):
                    pass

        if self._stype == 'capacitor':
            if isinstance(value, (str, Capacitance)):
                try:
                    return gsymlib.find_capacitor(value, footprint, device)
                except (gsymlib.NoGedaSymbolException, InvalidOperation):
                    pass

        ident = electronics.ident_transform(device, value, footprint)
        return gsymlib.get_symbol(ident)

    def get_type_value(self, value):
        if self._stype == 'capacitor':
            capacitance, voltage = electronics.parse_capacitor(value)
            return self._typeclass(capacitance)
        if self._stype == 'resistor':
            resistance, wattage = electronics.parse_resistor(value)
            return self._typeclass(resistance)

    def get_closest_value(self, target, heuristic=None):
        if heuristic == '+':
            raise NotImplementedError
        elif heuristic == '-':
            raise NotImplementedError
        elif heuristic is None:
            ldelta = None
            lvalue = None
            for value in self.gen_vals(self._stype):
                if value == target:
                    return value
                if value > target:
                    if ldelta is None:
                        return value
                    else:
                        ndelta = target - value
                        if abs(ndelta) < abs(ldelta):
                            return value
                        else:
                            return lvalue
                ldelta = target - value
                lvalue = value
        else:
            raise AttributeError

    def get_characteristic_value(self):
        s = 0
        n = 0
        for value in self.gen_vals(self._stype):
            s += log10(float(value))
            n += 1
        return self._typeclass(10 ** (s/n))


class IEC60063ValueSeries(ValueSeries):
    def __init__(self, series, stype, start=None, end=None,
                 device=None, footprint=None):
        super(IEC60063ValueSeries, self).__init__(stype, start, end,
                                                  device, footprint)
        self._series = iec60063.get_series(series)
        self._ostrs = iec60063.get_ostr(stype)

    def gen_vals(self, stype=None, start=None, end=None):
        if stype != self._stype:
            raise TypeError('This {0} series is not defined for {1}'
                            ''.format(self._stype, stype))
        if start is None:
            start = self._start
        if end is None:
            end = self._end
        for value in iec60063.gen_vals(self._series, self._ostrs,
                                       start=start, end=end):
            yield self._typeclass(value)


class CustomValueSeries(ValueSeries):
    def __init__(self, name, stype, start=None, end=None,
                 device=None, footprint=None):
        super(CustomValueSeries, self).__init__(
                stype, start, end, device, footprint
        )
        self._name = name
        self._values = {}
        self._desc = None
        self._aparams = {}
        if self._start is not None:
            if not isinstance(self._start, self._typeclass):
                self._start = self._typeclass(self._start)
        if self._end is not None:
            if not isinstance(self._end, self._typeclass):
                self._end = self._typeclass(self._end)

    def add_value(self, type_value, value):
        if not isinstance(type_value, self._typeclass):
            type_value = self._typeclass(type_value)
        type_value = str(type_value)
        self._values[type_value] = value

    def _value_generator(self, start=None, end=None):
        values = sorted([self._typeclass(x) for x in self._values.keys()])
        for value in values:
            if start is not None and value < start:
                continue
            if end is not None and value > end:
                break
            yield value

    def gen_vals(self, stype=None, start=None, end=None):
        if stype and stype != self._stype:
            raise ValueError("{0} is not an allowed stype for the {1} series!"
                             "".format(stype, self._name))
        return self._value_generator(start=start, end=end)

    def get_partno(self, value):
        if isinstance(value, self._typeclass):
            value = str(value)
        return self._values[value]

    def get_symbol(self, value, device=None, footprint=None):
        if isinstance(value, self._typeclass):
            value = str(value)
        return super(CustomValueSeries, self).get_symbol(
                self._values[value], device, footprint
        )

    def get_type_value(self, value):
        for type_value, lvalue in self._values.iteritems():
            if lvalue == value:
                return self._typeclass(type_value)


# TODO Improve isolation from gedaif
custom_series = {}


def get_series(series, stype, start=None, end=None,
               device=None, footprint=None):
    try:
        return IEC60063ValueSeries(
                series, stype, start=start, end=end,
                device=device, footprint=footprint
        )
    except ValueError:
        from tendril.gedaif.gsymlib import custom_series
        cseries = copy.deepcopy(custom_series[series])
        assert stype == cseries._stype
        if start is not None:
            cseries._start = start
        if end is not None:
            cseries._end = end
        if device is not None:
            assert device == cseries._device
        if footprint is not None:
            assert footprint == cseries._footprint
        return cseries
