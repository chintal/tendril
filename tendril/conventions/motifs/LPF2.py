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

"""

from math import pi
from math import sqrt
from math import log10
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

        # Set Frequency
        assert configdict['poly'] in ['Butterworth', 'Bessel']
        self.poly = configdict['poly']
        self.Fc = configdict['Fc']

        self._process()
        self.validate()

    def _process(self):
        # # TODO improve this calculation
        if self.poly == 'Butterworth':
            num, den = signal.butter(2, 1, 'lowpass', analog=True, output='ba')
            self._a = den[1]
            self._b = den[0]
            self._tgt_Q = sqrt(self._b) / self._a
        elif self.poly == 'Bessel':
            raise NotImplementedError
        else:
            raise ValueError

        best = None
        for ci in self.c1series.gen_vals('capacitor'):
            try:
                self._populate_components(ci)
            except ValueError:
                continue
            score = self.Score
            if best is None:
                best = (ci, score)
            elif score > best[1]:
                best = (ci, score)

        self._Ci = best[0]
        self._populate_components(self._Ci)

    def _populate_components(self, Ci):
        # Set C1 to initial guess
        cC1 = Ci
        cC1 = self._set_component('C1', cC1, self.c1series)

        # Set C2 to nearest match
        self.mCR = 4 * self._b / (self._a ** 2)
        cC2 = cC1 * self.mCR * 1.1
        cC2 = self._set_component('C2', cC2, self.c2series)

        # Set R1 and R2
        tn1 = self._a * float(cC2)
        tn2 = (self._a * float(cC2)) ** 2 - 4 * self._b * float(cC1) * float(
            cC2)
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
    def Score(self):
        score = 1.0

        # Gain settings
        ke_fc = 10.0
        ke_q = 10.0
        ke_r = 0.01
        ke_c = 0.005

        # Fc correctness
        e_fc = ke_fc * log10(self.Fc / self._tgt_Fc)
        score *= (1 - abs(e_fc))

        # Q correctness
        e_q = ke_q * log10(self.Q / self._tgt_Q)
        score *= (1 - abs(e_q))

        # Component range
        e_R1 = ke_r * log10(self.R1 / self.r1series.get_characteristic_value())
        score *= (1 - abs(e_R1))
        e_R2 = ke_r * log10(self.R2 / self.r2series.get_characteristic_value())
        score *= (1 - abs(e_R2))
        e_C1 = ke_c * log10(self.C1 / self.c1series.get_characteristic_value())
        score *= (1 - abs(e_C1))
        e_C2 = ke_c * log10(self.C2 / self.c2series.get_characteristic_value())
        score *= (1 - abs(e_C2))

        return round(score, 5)

    @property
    def _r1r2c1c2(self):
        return float(self.R1) * float(self.R2) * float(self.C1) * float(self.C2)

    @property
    def a1(self):
        r = float(self.C1) * float(self.R1 + self.R2) * 2 * pi * float(self.Fc)
        return round(r, 5)

    @property
    def b1(self):
        r = (2 * pi * float(self.Fc)) ** 2 * self._r1r2c1c2
        return round(r, 5)

    @property
    def Fc(self):
        return Frequency(1 / (2 * pi * sqrt(self._r1r2c1c2)))

    @property
    def Q(self):
        q = sqrt(self._r1r2c1c2) / (float(self.R1 + self.R2) * float(self.C1))
        return round(q, 5)

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
        assert self.Score > 0.9

    def get_configdict_stub(self):
        stub = {'desc': "Second Order Sallen-Key Low Pass Filter",
                'Fc': "15000Hz", 'poly': 'Butterworth',
                'Rseries': "E24", 'Rmin': '470E', 'Rmax': '47K',
                'Cseries': "E6", 'Cmin': "100pF", 'Cmax': "22uF",
                }
        return stub

    @property
    def listing(self):
        return [('Fc', self.Fc.quantized_repr),
                ('Q', self.Q)]

    @property
    def parameters_base(self):
        p_fc = [
            ('Fc', "Filter Cutoff Frequency", self._tgt_Fc),
            ('Q', "Filter Pole Quality", round(self._tgt_Q, 5)),
            ('Score', "Solution Score", 1)
        ]
        p_coeff = [
            ('a1', '', round(self._a, 5)),
            ('b1', '', round(self._b))
        ]
        p_intermediate = [
            ('CR', "Capacitance ratio (C2/C1)", ''.join(['>=', str(self.mCR)]))
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
            ('Rmin', '470E', 'Minimum Resistance', Resistance),
            ('Rmax', '47K', 'Maximum Resistance', Resistance),
            ('Fc', "15000Hz", 'Filter Cutoff Frequency', Frequency),
            ('poly', "Butterworth", 'Filter Polynomial', str),
        ]
        return inputs
