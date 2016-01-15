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
Docstring for snomap
"""

from .projects import cards
from .projects import get_module_snoseries
from .products import productlib

from .serialnos import get_serialno


class SerialNumberMap(object):
    def __init__(self, snomap_dict, efield=None):
        self._snomap_dict = snomap_dict
        self._generators = {}
        self._efield = efield
        self._register = None

        self.disable_creation()

    def enable_creation(self):
        self._register = True

    def disable_creation(self):
        self._register = False

    def dump_to_file(self, outfolder):
        pass

    def load_from_file(self, inpath):
        pass

    def mapped_snos(self, key):
        if key in self._snomap_dict.keys():
            return self._snomap_dict[key]

    def get_sno(self, key):
        if key not in self._generators:
            self._generators[key] = self._sno_generator(key)
        try:
            return next(self._generators[key])
        except StopIteration:
            raise OverflowError("Could not generate serial number for {0}. "
                                "We seem to have run out!".format(key))

    def _sno_generator(self, key):
        if key in self._snomap_dict.keys():
            for sno in self._snomap_dict[key]:
                yield sno
        # generate new from here
        if key == 'indentsno':
            while True:
                yield get_serialno(series='IDT',
                                   efield='FOR {0}'.format(self._efield),
                                   register=self._register)
        elif key in cards:
            # Get card information and generate sno accordingly.
            while True:
                yield get_serialno(series=get_module_snoseries(key),
                                   efield=key,
                                   register=self._register)
        elif key in [x.name for x in productlib]:
            # Get product information and generate sno accordingly.
            # Currently, all products derive their sno from the core. As such,
            # no serial numbers can be generated on the product itself. Update
            # this bit when that changes.
            raise ValueError("Can't generate serial number for "
                             "the product {0}".format(key))
        else:
            raise ValueError("Can't generate serial number for the "
                             "unknown entity {0}".format(key))


