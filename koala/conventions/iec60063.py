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
Preferred Values IEC60063 Module documentation (:mod:`conventions.iec60063`)
============================================================================
"""

from decimal import Decimal

E24 = map(Decimal, ['1.0', '1.1', '1.2', '1.3', '1.5', '1.6', '1.8', '2.0', '2.2', '2.4', '2.7', '3.0',
                    '3.3', '3.6', '3.9', '4.3', '4.7', '5.1', '5.6', '6.2', '6.8', '7.5', '8.2', '9.1'])
E12 = [elem for idx, elem in enumerate(E24) if idx % 2 == 0]
E6 = [elem for idx, elem in enumerate(E12) if idx % 2 == 0]
E3 = [elem for idx, elem in enumerate(E6) if idx % 2 == 0]

cap_ostrs = ['fF', 'pF', 'nF', 'uF', 'mF']
res_ostrs = ['m', 'E', 'K', 'M', 'G']
zen_ostrs = ['V']
ind_ostrs = ['nH', 'uH', 'mH']
num_ostrs = ['']


def get_ostr(stype):
    if stype == 'resistor':
        return res_ostrs
    if stype == 'capacitor':
        return cap_ostrs
    if stype == 'zener':
        return zen_ostrs
    if stype == 'inductor':
        return ind_ostrs
    return num_ostrs


def get_series(seriesst):
    if seriesst == 'E24':
        series = E24
    elif seriesst == 'E12':
        series = E12
    elif seriesst == 'E6':
        series = E6
    elif seriesst == 'E3':
        series = E3
    else:
        raise ValueError(seriesst)
    return series


def gen_vals(series, ostrs, start=None, end=None):
    if isinstance(series, str):
        series = get_series(series)
    if start is None:
        in_range = True
    else:
        in_range = False
    vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())
    for ostr in ostrs:
        for decade in range(3):
            for value in series:
                valstr = vfmt(value * (10 ** decade)) + ostr
                if in_range is False:
                    if valstr == start:
                        in_range = True
                if in_range is True:
                    yield valstr
                    if valstr == end:
                        return
