"""
EntityHub Maps Module documentation (:mod:`entityhub.maps`)
===========================================================
"""

import csv


class MapFile(object):
    def __init__(self, mappath):
        self._map = {}
        with open(mappath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                self._map[row[0]] = row[1:]

    def get_partnos(self, canonical):
        return self._map[canonical]

    def get_canonical(self, partno):
        for (k, v) in self._map:
            if partno in v:
                return k
        return None

