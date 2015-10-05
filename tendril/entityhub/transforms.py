# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
EntityHub Transforms Module documentation (:mod:`entityhub.transforms`)
=======================================================================
"""

import csv


class TransformFile(object):
    def __init__(self, tfpath):
        self._transform = {}
        self._ideal = {}
        self._status = {}
        with open(tfpath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                self._transform[row[0].strip()] = row[1].strip()
                self._ideal[row[0].strip()] = row[2].strip()
                try:
                    self._status[row[0].strip()] = row[3].strip()
                except IndexError:
                    self._status[row[0].strip()] = ''

    def get_canonical_repr(self, contextual):
        return self._transform[contextual.strip()]

    def get_ideal_repr(self, contextual):
        return self._ideal[contextual.strip()]

    def get_status(self, contextual):
        return self._status[contextual.strip()]

    def get_contextual_repr(self, canonical):
        for (k, v) in self._transform.iteritems():
            if v == canonical.strip():
                return k
        return None

    def has_contextual_repr(self, contextual):
        if contextual.strip() in self._transform.keys():
            return True
        else:
            return False
