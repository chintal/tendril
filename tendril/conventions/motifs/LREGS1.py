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

from math import fabs

import iec60063

from tendril.conventions.motifs.motifbase import MotifBase
from tendril.conventions import electronics
from tendril.gedaif import gsymlib

from tendril.utils.types.electromagnetic import Voltage
from tendril.utils.types.electromagnetic import Current
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MotifLREGS1(MotifBase):
    def __init__(self, identifier):
        super(MotifLREGS1, self).__init__(identifier)
        self._target_vout = None

    def configure(self, configdict):
        self._configdict = configdict
        self._target_vout = Voltage(configdict['Vout'])
        self._autoset_r2()
        self._autoset_r1()
        self.validate()

    def _autoset_r2(self):
        r2_dev = self.get_elem_by_idx('R2').data['device']
        r2_fp = self.get_elem_by_idx('R2').data['footprint']
        if r2_fp[0:3] == "MY-":
            r2_fp = r2_fp[3:]

        allowed_res_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        required_res_val = fabs(self.Vref.value / self.Imin.value)
        required_res_val = Resistance(required_res_val)

        rval = None
        for val in allowed_res_vals:
            lastval = rval
            rval = Resistance(val)
            if rval >= required_res_val:
                self.get_elem_by_idx('R2').data['value'] = gsymlib.find_resistor(lastval, r2_fp, r2_dev)  # noqa
                break

    def _autoset_r1(self):
        self.Vout = self._target_vout

    @property
    def Vout(self):
        return self.Vref * (1 + (self.R1 / self.R2))

    @Vout.setter
    def Vout(self, value):
        r1_dev = self.get_elem_by_idx('R1').data['device']
        r1_fp = self.get_elem_by_idx('R1').data['footprint']
        if r1_fp[0:3] == "MY-":
            r1_fp = r1_fp[3:]

        allowed_res_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        required_res_val = ((value / self.Vref) - 1) * self.R2

        rval = None
        for val in allowed_res_vals:
            lastval = rval
            rval = Resistance(val)
            if rval >= required_res_val:
                self.get_elem_by_idx('R1').data['value'] = gsymlib.find_resistor(lastval, r1_fp, r1_dev)  # noqa
                break

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def R2(self):
        elem = self.get_elem_by_idx('R2')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def Vref(self):
        return Voltage(self._configdict['Vref'])

    @property
    def Imin(self):
        return Current(self._configdict['Imin'])

    @property
    def Il(self):
        return Current(self.Vref.value / self.R2.value)

    @property
    def listing(self):
        return [('Vout', self.Vout.quantized_repr)]

    def validate(self):
        pass

    @property
    def parameters_base(self):
        p_vout = [
            ('R1', "Lower Feedback Resistor", ''),
            ('R2', "Upper Feedback Resistor", ''),
            ('Vout', "Actual Output Voltage", self._configdict['Vout']),
            ('Il', "Actual Minimum Load", self.Imin)
        ]
        parameters = [
            (p_vout, "Output Voltage Setting"),
        ]
        return parameters

    @property
    def configdict_base(self):
        inputs = [
            ('desc', 'Positive LDO Output Voltage Setter', 'description', str),
            ('Vref', '1.225V',
             'Internal Reference for Output Voltage Feedback', Voltage),
            ('Rseries', 'E24', 'Resistance Series', str),
            ('Rmin', '10E', 'Minimum Resistance', Resistance),
            ('Rmax', '10M', 'Maximum Resistance', Resistance),
            ('Imin', '1mA', 'Minimum Load Current for Regulation', Current),
            ('Vout', '', 'Output Voltage', Voltage),
        ]
        return inputs
