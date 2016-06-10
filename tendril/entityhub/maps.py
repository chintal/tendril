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

import os
import csv

from tendril.utils.config import VENDOR_MAP_FOLDER
from tendril.utils.fsutils import VersionedOutputFile
from tendril.utils.fsutils import get_file_mtime

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


class MapFileBase(object):
    def __init__(self, mappath, name=None):
        self._mappath = mappath
        if name is None:
            self._name = os.path.splitext(os.path.split(mappath)[1])[0]
        else:
            self._name = name

    def _dump_mapfile(self):
        outpath = os.path.join(VENDOR_MAP_FOLDER, self._mappath)
        outf = VersionedOutputFile(outpath)
        outw = csv.writer(outf)
        outw.writerow(('Canonical', 'Strategy', 'Lparts'))
        for ident in self.get_idents():
            outw.writerow(
                [ident, (self.get_strategy(ident) or '')] +
                self.get_upartnos(ident) +
                ['@AG@' + x for x in self.get_apartnos(ident)]
            )
        outf.close()
        logger.info("Dumped {0} Vendor Map to File : {1}"
                    "".format(self._name, outpath))

    def get_idents(self):
        raise NotImplementedError

    def get_map_time(self, canonical):
        raise NotImplementedError

    def get_upartnos(self, canonical):
        raise NotImplementedError

    def get_apartnos(self, canonical):
        raise NotImplementedError

    def get_partnos(self, canonical):
        uparts = self.get_upartnos(canonical)
        if len(uparts) > 0:
            return uparts
        aparts = self.get_apartnos(canonical)
        if len(aparts) > 0:
            return aparts
        return []

    def get_all_partnos(self, canonical):
        return self.get_upartnos(canonical) + self.get_apartnos(canonical)

    def get_strategy(self, canonical):
        raise NotImplementedError

    def get_canonical(self, partno):
        raise NotImplementedError

    def get_user_map(self):
        raise NotImplementedError

    def length(self):
        raise NotImplementedError

    def remove_apartno(self, partno, canonical):
        raise NotImplementedError


class MapFile(MapFileBase):
    # Deprecated.
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

    def get_map_time(self, canonical):
        return get_file_mtime(self._mappath)

    def get_upartnos(self, canonical):
        return self._umap[canonical]

    def get_apartnos(self, canonical):
        return self._map[canonical]

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
