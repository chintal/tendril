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

import os

from .projects import cards
from .projects import get_module_snoseries
from .products import productlib

from .serialnos import get_serialno
from .serialnos import link_serialno

from tendril.utils.files import yml as yaml


class SerialNumberMap(object):
    def __init__(self, snomap_dict=None, parent_sno=None):
        if snomap_dict is None:
            snomap_dict = {}
        self._snomap_dict = snomap_dict
        self._generators = {}
        self._parent_sno = parent_sno
        self._register = None
        self._session = None
        self.disable_creation()

    def enable_creation(self):
        self._register = True

    def set_session(self, session=None):
        self._session = session

    def unset_session(self):
        self._session = None

    def disable_creation(self):
        self._register = False
        self._session = None

    def dump_to_file(self, outfolder):
        with open(os.path.join(outfolder, 'snomap.yaml'), 'w') as f:
            self._snomap_dict['parentsno'] = self._parent_sno
            f.write(yaml.dump(self._snomap_dict, default_flow_style=False))

    def load_from_file(self, inpath):
        pass

    def map_keys(self):
        return self._snomap_dict.keys()

    def mapped_snos(self, key):
        if key in self._snomap_dict.keys():
            if isinstance(self._snomap_dict[key], dict):
                return [x for idx, x in self._snomap_dict[key].iteritems()]
            else:
                return [self._snomap_dict[key]]
        else:
            raise KeyError("This snomap does not seem to include"
                           "any serial numbers for {0}".format(key))

    def get_sno(self, key):
        if key not in self._generators:
            self._generators[key] = self._sno_generator(key)
        try:
            return next(self._generators[key])
        except StopIteration:
            raise OverflowError("Could not generate serial number for {0}. "
                                "We seem to have run out!".format(key))

    def _sno_generator(self, key):
        count = 0
        if key not in self._snomap_dict.keys():
            self._snomap_dict[key] = {}
        if isinstance(self._snomap_dict[key], dict):
            for idx, sno in self._snomap_dict[key].iteritems():
                count += 1
                yield sno
        elif isinstance(self._snomap_dict[key], list):
            for sno in self._snomap_dict[key]:
                count += 1
                yield sno
        else:
            count += 1
            yield self._snomap_dict[key]
        # generate new from here
        if key == 'indentsno':
            while True:

                sno = get_serialno(series='IDT',
                                   efield='FOR {0}'.format(self._parent_sno),
                                   register=self._register,
                                   session=self._session)
                if self._register:
                    link_serialno(child=sno, parent=self._parent_sno,
                                  session=self._session)
                count += 1
                if isinstance(self._snomap_dict[key], dict):
                    self._snomap_dict[key][count] = sno
                elif isinstance(self._snomap_dict[key], list):
                    self._snomap_dict[key].append(sno)
                else:
                    self._snomap_dict[key] = {
                        1: self._snomap_dict[key],
                        2: sno,
                    }
                yield sno

        elif key in cards:
            # Get card information and generate sno accordingly.
            while True:
                sno = get_serialno(series=get_module_snoseries(key),
                                   efield=key,
                                   register=self._register,
                                   session=self._session)
                if self._register:
                    link_serialno(child=sno, parent=self._parent_sno,
                                  session=self._session)
                count += 1
                if isinstance(self._snomap_dict[key], dict):
                    self._snomap_dict[key][count] = sno
                elif isinstance(self._snomap_dict[key], list):
                    self._snomap_dict[key].append(sno)
                else:
                    self._snomap_dict[key] = {
                        1: self._snomap_dict[key],
                        2: sno,
                    }
                yield sno

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


