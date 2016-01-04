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

import re
import csv
from tendril.utils import fsutils
from tendril.gedaif import gsymlib


rex_known_status = re.compile(ur'ok|bad|review|new', re.IGNORECASE)


class ContextualReprNotRecognized(Exception):
    pass


class NoCanonicalReprInContext(Exception):
    pass


class TransformFile(object):
    def __init__(self, tfpath):
        self._transform = {}
        self._ideal = {}
        self._status = {}
        self._tfpath = tfpath
        self.load_from_disk()

    def load_from_disk(self):
        self._transform = {}
        self._ideal = {}
        self._status = {}
        with open(self._tfpath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                contextual = row[0].strip()
                self._transform[contextual] = row[1].strip()
                self._ideal[contextual] = row[2].strip()
                try:
                    self._status[contextual] = row[3].strip()
                except IndexError:
                    self._status[contextual] = ''

    def update_on_disk(self):
        # TODO this function makes the implementation somewhat specific
        # to inventory transforms. Consider refactoring.
        outf = fsutils.VersionedOutputFile(self._tfpath)
        outw = csv.writer(outf)
        outw.writerow(
            ('Current', 'gEDA Current', 'Ideal', 'Status', 'In Symlib')
        )
        for name in self.names:
            canonical = self.get_canonical_repr(name)
            if gsymlib.is_recognized(canonical):
                in_symlib = 'YES'
            else:
                in_symlib = ''
            outw.writerow((name,
                           canonical,
                           self.get_ideal_repr(name),
                           self.get_status(name),
                           in_symlib,))
        outf.close()

    def set_canonical_repr(self, contextual, canonical):
        self._transform[contextual] = canonical

    def set_status(self, contextual, status):
        if rex_known_status.match(status):
            status = status.upper()
        self._status[contextual] = status

    def get_canonical_repr(self, contextual):
        try:
            return self._transform[contextual.strip()]
        except KeyError:
            raise ContextualReprNotRecognized(contextual)

    def get_ideal_repr(self, contextual):
        try:
            return self._ideal[contextual.strip()]
        except KeyError:
            raise ContextualReprNotRecognized(contextual)

    def get_status(self, contextual):
        try:
            return self._status[contextual.strip()]
        except KeyError:
            raise ContextualReprNotRecognized(contextual)

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

    @property
    def idents(self):
        return set(self._transform.values())

    @property
    def names(self):
        return set(self._transform.keys())
