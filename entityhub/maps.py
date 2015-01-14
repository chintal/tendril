"""
EntityHub Maps Module documentation (:mod:`entityhub.maps`)
===========================================================
"""

import csv


class MapFile(object):
    def __init__(self, mappath):
        self._map = {}
        self._umap = {}
        self._strategy = {}
        with open(mappath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                if row[0] == "Canonical":
                    continue
                self._strategy[row[0]] = row[1]
                vals = row[2:]
                self._map[row[0]] = []
                self._umap[row[0]] = []
                for elem in vals:
                    assert isinstance(elem, str)
                    if elem.startswith('@AG@'):
                        elem = elem[4:]
                        self._map[row[0]].append(elem)
                    else:
                        self._umap[row[0]].append(elem)

    def get_idents(self):
        return self._map.keys()

    def get_upartnos(self, canonical):
        return self._umap[canonical]

    def get_apartnos(self, canonical):
        return self._map[canonical]

    def get_all_partnos(self, canonical):
        return self._umap[canonical] + self._map[canonical]

    def get_partnos(self, canonical):
        if len(self._umap[canonical]) > 0:
            return self._umap[canonical]
        elif len(self._map[canonical]) > 0:
            return self._map[canonical]
        else:
            return []

    def get_strategy(self, canonical):
        return self._strategy[canonical]

    def get_canonical(self, partno):
        for (k, v) in self._umap:
            if partno in v:
                return k
        for (k, v) in self._map:
            if partno in v:
                return k
        return None

    def get_user_map(self):
        return self._umap

