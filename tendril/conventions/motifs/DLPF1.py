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

This file needs to be refactored quite a bit
"""

from math import pi

import iec60063

from tendril.conventions import electronics
from tendril.conventions.motifs.motifbase import MotifBase
from tendril.gedaif import gsymlib

# TODO change implementation to use units instead of numbers
from tendril.utils.types.electromagnetic import Capacitance  # noqa
from tendril.utils.types.electromagnetic import Resistance  # noqa
from tendril.utils.types.time import Frequency

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MotifDLPF1(MotifBase):
    def __init__(self, identifier):
        super(MotifDLPF1, self).__init__(identifier)

    def configure(self, configdict):
        # Set Resistances
        self.get_elem_by_idx('R1').data['value'] = electronics.construct_resistor(configdict['R1'], '0.125W')  # noqa
        self.get_elem_by_idx('R2').data['value'] = electronics.construct_resistor(configdict['R1'], '0.125W')  # noqa
        # Set Frequency
        self._configdict = configdict
        self.Fdiff = float(configdict['Fdiff'][:-2])
        self._set_biases()
        self.validate()

    def _set_biases(self):
        if 'pbias' not in self._configdict.keys():
            logger.warning(
                'Positive terminal bias not defined : ' + self.refdes
            )
        else:
            if self._configdict['pbias'] != '-1':
                self.get_elem_by_idx('R3').data['value'] = electronics.construct_resistor(self._configdict['pbias'], '0.125W')  # noqa
            else:
                try:
                    self.get_elem_by_idx('R3').data['fillstatus'] = 'DNP'
                except KeyError:
                    pass

        if 'nbias' not in self._configdict.keys():
            logger.warning(
                'Negative terminal bias not defined : ' + self.refdes
            )
        else:
            if self._configdict['nbias'] != '-1':
                self.get_elem_by_idx('R4').data['value'] = electronics.construct_resistor(self._configdict['nbias'], '0.125W')  # noqa
            else:
                try:
                    self.get_elem_by_idx('R4').data['fillstatus'] = 'DNP'
                except KeyError:
                    pass

    @property
    def Fdiff(self):
        return Frequency(1 / (2 * pi * float(self.R1) * float(2 * self.C1 + self.C2)))  # noqa

    @property
    def Fcm(self):
        return 1 / (2 * pi * float(self.R1) * float(self.C2))

    @Fdiff.setter
    def Fdiff(self, value):
        c1_dev = self.get_elem_by_idx('C1').data['device']
        c1_fp = self.get_elem_by_idx('C1').data['footprint']
        if c1_fp[0:3] == "MY-":
            c1_fp = c1_fp[3:]

        allowed_cap_vals = iec60063.gen_vals(self._configdict['Cseries'],
                                             iec60063.cap_ostrs,
                                             self._configdict['Cmin'],
                                             self._configdict['Cmax'])

        fcm_est = value * 21
        required_cap_val = 1 / (2 * pi * float(self.R1) * fcm_est)

        cval = None
        lastval = None
        for val in allowed_cap_vals:
            lastval = cval
            cval = electronics.parse_capacitance(val)
            if cval >= required_cap_val:
                self.get_elem_by_idx('C2').data['value'] = gsymlib.find_capacitor(lastval, c1_fp, c1_dev).value  # noqa
                self.get_elem_by_idx('C3').data['value'] = gsymlib.find_capacitor(lastval, c1_fp, c1_dev).value  # noqa
                break

        if cval is None:
            raise ValueError

        required_cap_val = lastval * 10
        for val in allowed_cap_vals:
            cval = electronics.parse_capacitance(val)
            if cval >= required_cap_val:
                self.get_elem_by_idx('C1').data['value'] = gsymlib.find_capacitor(cval, c1_fp, c1_dev).value  # noqa
                break

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0])  # noqa

    @property
    def R2(self):
        elem = self.get_elem_by_idx('R2')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0])  # noqa

    @property
    def C1(self):
        elem = self.get_elem_by_idx('C1')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return electronics.parse_capacitance(electronics.parse_capacitor(elem.data['value'])[0])  # noqa

    @property
    def C2(self):
        elem = self.get_elem_by_idx('C2')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return electronics.parse_capacitance(electronics.parse_capacitor(elem.data['value'])[0])  # noqa

    @property
    def C3(self):
        elem = self.get_elem_by_idx('C3')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return electronics.parse_capacitance(electronics.parse_capacitor(elem.data['value'])[0])  # noqa

    def validate(self):
        logger.debug("Validating Motif : " + self.refdes)
        assert self.R1 == self.R2
        assert self.C3 == self.C2
        try:
            assert self.C1 >= 10 * self.C2
        except AssertionError:
            print 'C1 ' + str(self.C1)
            print 'C2 ' + str(self.C2)
            # raise

    @property
    def parameters_base(self):
        p_fc = [
            ('Fdiff', "Differential Cutoff Frequency", ''),
            ('Fcm', "Common Mode Cutoff Frequency", ''),
        ]
        parameters = [
            (p_fc, "Filter Parameters"),
        ]
        return parameters

    @property
    def configdict_base(self):
        inputs = [
            ('desc', "Differential Low Pass RFI and AAF filter",
             'description', str),
            ('Cseries', 'E6', 'Capacitance Series', str),
            ('Cmin', '1pF', 'Minimum Capacitance', str),
            ('Cmax', '100nF', 'Maximum Capacitance', str),
            ('Fdiff', "15000Hz", 'Differential Cutoff Frequency', str),
            ('R1', "50E", 'Input Resistance Value', str),
            ('pbias', '-1', 'IN+ Bias', str),
            ('nbias', '-1', 'IN- Bias', str),
        ]
        return inputs
