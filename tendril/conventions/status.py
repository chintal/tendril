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
Docstring for status
"""

import numbers


STATUS_ORDER = {
    'Prototype': (10, None),
    'Active': (20, 'success'),
    'Deprecated': (30, 'warning'),
    'Suspended': (40, 'disabled'),
    'Prospective': (50, 'info'),
    'Experimental': (60, 'warning'),
    'Archived': (70, 'secondary'),
    'Discarded': (80, 'alert'),
}


class Status(object):
    def __init__(self, ststr):
        self._ststr = ststr
        self._stint = STATUS_ORDER[ststr][0]
        self._sthtml = STATUS_ORDER[ststr][1]

    def __repr__(self):
        return self._ststr

    def __str__(self):
        return self._ststr

    @property
    def html_class(self):
        return self._sthtml

    @property
    def num(self):
        return self._stint

    def __eq__(self, other):
        # TODO Fix for thorough string handling
        if isinstance(other, str):
            return other == self._ststr
        if isinstance(other, numbers.Number):
            return other == self._stint
        if isinstance(other, Status):
            return other._stint == self._stint
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, Status):
            return self._stint < other._stint
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Status):
            return self._stint <= other._stint
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Status):
            return self._stint > other._stint
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Status):
            return self._stint >= other._stint
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Status):
            return self._stint != other._stint


status_objects = {}


def get_status(ststr):
    if ststr not in status_objects.keys():
        status_objects[ststr] = Status(ststr)
    return status_objects[ststr]


def get_known_statuses():
    rval = []
    for k in STATUS_ORDER.keys():
        rval.append(get_status(k))
    return sorted(rval)