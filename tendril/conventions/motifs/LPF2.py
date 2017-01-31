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

Based heavily on
https://focus.ti.com/lit/ml/sloa088/sloa088.pdf

Verifications based on
http://www.daycounter.com/Filters/SallenKeyLP/Sallen-Key-LP-Filter-Design-Equations.phtml
http://sim.okawa-denshi.jp/en/OPstool.php

TODO
The initial guess for C1 is actually a fixed value of C1. This needs to be
automatically chosen.
Using the initial C1, the other numbers are all just set per series. This
should be augmented to take into account the fact that the closest match in
the series may well be far from ideal.
"""

from decimal import Decimal
from math import pi
from math import sqrt
from scipy import signal

from tendril.conventions.motifs.motifbase import MotifBase
from tendril.utils import log
from tendril.utils.types.electromagnetic import Capacitance
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.time import Frequency

logger = log.get_logger(__name__, log.DEFAULT)


class MotifLPF2(MotifBase):
    def __init__(self, identifier):
        super(MotifLPF2, self).__init__(identifier)

    def configure(self, configdict):
        self._configdict = configdict

        # Get Series
        self.c1series = self._get_component_series('C1', 'capacitor')
        self.c2series = self._get_component_series('C2', 'capacitor')
        self.r1series = self._get_component_series('R1', 'resistor')
        self.r2series = self._get_component_series('R2', 'resistor')

        self.Ci = configdict['Ci']

        # Set Frequency
        assert configdict['poly'] in ['Butterworth', 'Bessel']
        self.poly = configdict['poly']
        self.Fc = configdict['Fc']

        self._process()
        self.validate()

    @property
    def Ci(self):
        return self._Ci

    @Ci.setter
    def Ci(self, value):
        self._Ci = Capacitance(value)

    def _process(self):
        # # TODO improve this calculation
        if self.poly == 'Butterworth':
            num, den = signal.butter(2, 1, 'lowpass', analog=True, output='ba')
            self._a = den[1]
            self._b = den[0]
        elif self.poly == 'Bessel':
            raise NotImplementedError
        else:
            raise ValueError

        # Set C1 to initial guess
        cC1 = self._Ci
        cC1 = self._set_component('C1', cC1, self.c1series)

        # Set C2 to nearest match
        self.mCR = 4 * self._b / (self._a ** 2)
        cC2 = cC1 * self.mCR * 1.1
        cC2 = self._set_component('C2', cC2, self.c2series)

        # Set R1 and R2
        tn1 = self._a * float(cC2)
        tn2 = (self._a * float(cC2))**2 - 4 * self._b * float(cC1) * float(cC2)
        tn2 = sqrt(tn2)
        td = 4 * pi * float(self._tgt_Fc) * float(cC1) * float(cC2)

        rR1 = Resistance((tn1 + tn2) / td)
        rR1 = self._set_component('R1', rR1, self.r1series)
        rR2 = Resistance((tn1 - tn2) / td)
        rR2 = self._set_component('R2', rR2, self.r2series)

    def _set_component(self, refdes, target, series):
        value = series.get_closest_value(target)
        if not value:
            raise ValueError
        try:
            svalue = series.get_symbol(value).value
        except AttributeError:
            svalue = series.get_symbol(value)
        self.get_elem_by_idx(refdes).data['value'] = svalue  # noqa
        return series.get_type_value(svalue)

    @property
    def _r1r2c1c2(self):
        return float(self.R1) * float(self.R2) * float(self.C1) * float(self.C2)

    @property
    def a1(self):
        return float(self.C1) * float(self.R1 + self.R2) * 2 * pi * float(self.Fc)

    @property
    def b1(self):
        return (2 * pi * float(self.Fc)) ** 2 * self._r1r2c1c2

    @property
    def Fc(self):
        return Frequency(1 / (2 * pi * sqrt(self._r1r2c1c2)))

    @property
    def Q(self):
        return sqrt(self._r1r2c1c2) / (float(self.R1 + self.R2) * float(self.C1))

    @Q.setter
    def Q(self, value):
        self._tgt_Q = Decimal(value)

    @Fc.setter
    def Fc(self, value):
        self._tgt_Fc = Frequency(value)

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return self.r1series.get_type_value(elem.data['value'])

    @property
    def R2(self):
        elem = self.get_elem_by_idx('R2')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return self.r2series.get_type_value(elem.data['value'])

    @property
    def C1(self):
        elem = self.get_elem_by_idx('C1')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return self.c1series.get_type_value(elem.data['value'])

    @property
    def C2(self):
        elem = self.get_elem_by_idx('C2')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return self.c2series.get_type_value(elem.data['value'])

    @property
    def CR(self):
        return self.C2 / self.C1

    def validate(self):
        pass

    def get_configdict_stub(self):
        stub = {'desc': "Second Order Sallen-Key Low Pass Filter",
                'Fc': "15000Hz", 'poly': 'Butterworth',
                'Rseries': "E24", 'Rmin': '100E', 'Rmax': '100K',
                'Cseries': "E6", 'Cmin': "100pF", 'Cmax': "22uF",
                'Ci': '470pF',
                }
        return stub

    @property
    def listing(self):
        return [('Fc', self.Fc), ('Q', self.Q)]

    @property
    def parameters_base(self):
        p_fc = [
            ('Fc', "Filter Cutoff Frequency", self._tgt_Fc),
            ('poly', "Filter Polynomial", ''),
            ('Q', "Filter Pole Quality", sqrt(self._b) / (self._a)),
        ]
        p_coeff = [
            ('a1', '', self._a),
            ('b1', '', self._b)
        ]
        p_intermediate = [
            ('Ci', "Capacitance Guess", self._configdict['Ci']),
            ('CR', "Capacitance ratio (C2/C1)", self.mCR)
        ]
        parameters = [
            (p_fc, "Filter Parameters"),
            (p_coeff, "Normalized Filter Coefficients"),
            (p_intermediate, "Intermediate Calculations")
        ]
        return parameters

    @property
    def configdict_base(self):
        inputs = [
            ('desc', "Simple Single Pole Low Pass Filter", 'description', str),
            ('Cseries', 'E6', 'Capacitance Series', str),
            ('Cmin', '100pF', 'Minimum Capacitance', Capacitance),
            ('Cmax', '22uF', 'Maximum Capacitance', Capacitance),
            ('Rseries', 'E6', 'Resistance Series', str),
            ('Rmin', '1pF', 'Minimum Resistance', Resistance),
            ('Rmax', '100nF', 'Maximum Resistance', Resistance),
            ('Fc', "15000Hz", 'Filter Cutoff Frequency', Frequency),
            ('poly', "Butterworth", 'Filter Polynomial', str),
            ('Ci', "470pF", 'Inital Capacitance Guess', Capacitance)
        ]
        return inputs
