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
EntityHub Maps Module documentation (:mod:`entityhub.maps`)
===========================================================
"""

import csv


class MapFileBase(object):
    def __init__(self, mappath):
        pass

    def _dump_mapfile(self):
        # outp = vendor_obj.mappath
        # outf = fsutils.VersionedOutputFile(outp)
        # outw = csv.writer(outf)
        # outw.writerow(('Canonical', 'Strategy', 'Lparts'))
        pass

    def get_idents(self):
        raise NotImplementedError

    def get_upartnos(self, canonical):
        raise NotImplementedError

    def get_apartnos(self, canonical):
        raise NotImplementedError

    def get_strategy(self, canonical):
        raise NotImplementedError

    def get_canonical(self, partno):
        raise NotImplementedError

    def get_user_map(self):
        raise NotImplementedError

    def length(self):
        raise NotImplementedError


class MapFile(MapFileBase):
    def __init__(self, mappath):
        super(MapFile, self).__init__(mappath)
        self._map = {}
        self._umap = {}
        self._strategy = {}
        self._len = 0
        self._mappath = mappath
        self._load_mapfile()

    def _load_mapfile(self):
        with open(self._mappath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                if row[0] == "Canonical":
                    continue
                ident = row[0]
                self._strategy[ident] = row[1]
                vals = row[2:]
                self._map[ident] = []
                self._umap[ident] = []
                for elem in vals:
                    assert isinstance(elem, str)
                    self._len += 1
                    if elem.startswith('@AG@'):
                        elem = elem[4:]
                        self._map[ident].append(elem)
                    else:
                        self._umap[ident].append(elem)

    def get_idents(self):
        for key in sorted(self._map.keys()):
            if len(self._map[key]) or len(self._umap[key]):
                yield key

    def get_upartnos(self, canonical):
        return self._umap[canonical]

    def get_apartnos(self, canonical):
        return self._map[canonical]

    def get_partnos(self, canonical):
        if canonical not in self.get_idents():
            return []
        if len(self._umap[canonical]) > 0:
            return self._umap[canonical]
        elif len(self._map[canonical]) > 0:
            return self._map[canonical]
        else:
            return []

    def get_strategy(self, canonical):
        if canonical not in self.get_idents():
            return 'NOTRECOG'
        return self._strategy[canonical]

    def get_canonical(self, partno):
        if len(self._umap) > 0:
            for (k, v) in self._umap.iteritems():
                if partno in v:
                    return k
        if len(self._map) > 0:
            for (k, v) in self._map.iteritems():
                if partno in v:
                    return k
        return None

    def get_user_map(self):
        return self._umap

    def length(self):
        return self._len
