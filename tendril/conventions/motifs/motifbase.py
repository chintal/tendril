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
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

from tendril.conventions import series


class MotifBase(object):
    columns = ['refdes', 'device', 'value', 'footprint',
               'fillstatus', 'group', 'package', 'status']

    def __init__(self, identifier):
        self._type = None
        self._ident = None
        self._elements = []
        self.refdes = identifier
        self._configdict = None

    @property
    def refdes(self):
        return self._type + '.' + self._ident

    @refdes.setter
    def refdes(self, value):
        value = value.split(':')[0]
        self._type, self._ident = value.split('.')

    @property
    def desc(self):
        return self._configdict['desc']

    @property
    def elements(self):
        return sorted(self._elements, key=lambda x: x.motif)

    def _line_generator(self):
        for elem in self._elements:
            yield elem

    def configure(self, configdict):
        raise NotImplementedError

    def get_line_gen(self):
        return self._line_generator()

    def get_elem_by_idx(self, idx):
        for elem in self._elements:
            if elem.data['motif'].split(':')[1] == idx:
                return elem
        raise KeyError(self.refdes, idx)

    def add_element(self, bomline):
        self._elements.append(bomline)

    def validate(self):
        raise NotImplementedError

    def __repr__(self):
        return "MOTIF OBJECT : " + self.refdes

    @property
    def listing(self):
        raise NotImplementedError

    @property
    def configdict_base(self):
        raise NotImplementedError

    def get_configdict_stub(self):
        stub = {}
        for parameter in self.configdict_base:
            stub[parameter[0]] = parameter[1]
        return stub

    @property
    def parameters_base(self):
        raise NotImplementedError

    @property
    def parameters(self):
        parameters = []
        for group in self.parameters_base:
            parameters.append(([
                (e[1], e[0], e[2], self.__getattribute__(e[0])) for e in group[0]  # noqa
            ], group[1]))
        return parameters

    @property
    def inputs(self):
        inputs = []
        for parameter in self.configdict_base:
            if parameter[0] is not 'desc':
                inputs.append((
                    parameter[0],
                    parameter[3](self._configdict[parameter[0]]),
                    parameter[2]
                ))
        return inputs

    def _get_component_series(self, refdes, type):
        if type == 'capacitor':
            stype = type
            sstr = 'Cseries'
            smin = 'Cmin'
            smax = 'Cmax'
        elif type == 'resistor':
            stype = type
            sstr = 'Rseries'
            smin = 'Rmin'
            smax = 'Rmax'
        else:
            raise NotImplementedError

        dev = self.get_elem_by_idx(refdes).data['device']
        fp = self.get_elem_by_idx(refdes).data['footprint']
        if fp[0:3] == "MY-":
            fp = fp[3:]
        return series.get_series(self._configdict[sstr],
                                 stype,
                                 start=self._configdict[smin],
                                 end=self._configdict[smax],
                                 device=dev,
                                 footprint=fp)
