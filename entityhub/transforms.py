"""
EntityHub Transforms Module documentation (:mod:`entityhub.transforms`)
=======================================================================
"""

import csv


class TransformFile(object):
    def __init__(self, tfpath):
        self._transform = {}
        with open(tfpath) as f:
            rdr = csv.reader(f)
            for row in rdr:
                self._transform[row[0]] = row[1]

    def get_canonical_repr(self, contextual):
        return self._transform[contextual]

    def get_contexual_repr(self, canonical):
        for (k, v) in self._transform:
            if v == canonical:
                return k
        return None
