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
                self._transform[row[0]] = row[1]
                self._ideal[row[0]] = row[2]
                try:
                    self._status[row[0]] = row[3]
                except IndexError:
                    self._status[row[0]] = ''

    def get_canonical_repr(self, contextual):
        return self._transform[contextual]

    def get_ideal_repr(self, contextual):
        return self._ideal[contextual]

    def get_status(self, contextual):
        return self._status[contextual]

    def get_contextual_repr(self, canonical):
        for (k, v) in self._transform:
            if v == canonical:
                return k
        return None

    def has_contextual_repr(self, contextual):
        if contextual in self._transform.keys():
            return True
        else:
            return False
