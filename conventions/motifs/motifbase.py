"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


class MotifBase(object):
    columns = ['refdes', 'device', 'value', 'footprint',
               'fillstatus', 'group', 'package', 'status']

    def __init__(self, identifier):
        self._type = None
        self._ident = None
        self._elements = []
        self.refdes = identifier

    @property
    def refdes(self):
        return self._type + '.' + self._ident

    @refdes.setter
    def refdes(self, value):
        value = value.split(':')[0]
        self._type, self._ident = value.split('.')

    def _line_generator(self):
        for elem in self._elements:
            yield elem

    def get_configdict_stub(self):
        raise NotImplementedError

    def configure(self, configdict):
        raise NotImplementedError

    def get_line_gen(self):
        return self._line_generator()

    def get_elem_by_idx(self, idx):
        for elem in self._elements:
            if elem.data['motif'].split(':')[1] == idx:
                return elem
        raise KeyError

    def add_element(self, bomline):
        self._elements.append(bomline)

    def validate(self):
        raise NotImplementedError
