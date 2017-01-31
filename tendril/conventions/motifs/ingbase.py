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


from tendril.conventions.motifs.motifbase import MotifBase

from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import VoltageGain

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MotifInampGainBase(MotifBase):
    def __init__(self, identifier):
        super(MotifInampGainBase, self).__init__(identifier)

    def configure(self, configdict):
        self._configdict = configdict
        self.target_gain = VoltageGain(configdict['gain'])
        self.gain = configdict['gain']
        self.validate()

    def res_to_gain(self, res):
        raise NotImplementedError

    def gain_to_res(self, gain):
        raise NotImplementedError

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        if elem.data['fillstatus'] == 'DNP':
            return None
        return self.rseries.get_type_value(elem.data['value'])

    @property
    def gain(self):
        return self.res_to_gain(self.R1)

    @gain.setter
    def gain(self, value):
        self.rseries = self._get_component_series('R1', 'resistor')
        allowed_res_vals = self.rseries.gen_vals('resistor')
        required_res_val = self.gain_to_res(value)

        if required_res_val and not isinstance(required_res_val, Resistance):
            required_res_val = Resistance(required_res_val)
        if required_res_val is None:
            self.get_elem_by_idx('R1').data['fillstatus'] = 'DNP'
            return

        lastval = None
        for rval in allowed_res_vals:
            if not lastval:
                lastval = rval
            if rval > required_res_val:
                try:
                    value = self.rseries.get_symbol(lastval).value
                except AttributeError:
                    value = self.rseries.get_symbol(lastval)
                self.get_elem_by_idx('R1').data['value'] = value  # noqa
                break
            lastval = rval

    @property
    def listing(self):
        return [('Gain', self.gain.quantized_repr)]

    @property
    def parameters_base(self):
        p_gain = [
            ('R1', "Gain Setting Resistance", ''),
            ('gain', "Amplifier DC Gain", self.target_gain),
        ]
        parameters = [
            (p_gain, "Gain Setting"),
        ]
        return parameters

    @property
    def configdict_base(self):
        inputs = [
            ('desc', 'Instrumentation Amplifier Gain', 'description', str),
            ('Rseries', 'E24', 'Resistance Series', str),
            ('Rmin', '10E', 'Minimum Resistance', str),
            ('Rmax', '10M', 'Maximum Resistance', str),
            ('gain', "1", 'Amplifier DC gain', str),
        ]
        return inputs

    def validate(self):
        pass
