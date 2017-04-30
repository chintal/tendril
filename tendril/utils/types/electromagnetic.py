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

import re

from unitbase import UnitBase
from unitbase import NumericalUnitBase
from unitbase import Percentage
from unitbase import GainBase
from unitbase import parse_none


class Resistance(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[\d]+\.?[\d]*)\s?(?P<order>[umEKMGT])(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['u', 'm', 'E', 'K', 'M', 'G', 'T']
    _dostr = 'E'


class Capacitance(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[\d]+\.?[\d]*)\s?(?P<order>[pnum]?F?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['fF', 'pF', 'nF', 'uF', 'mF', 'F']
    _dostr = 'F'
    _osuffix = 'F'


class Inductance(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[\d]+\.?[\d]*)\s?(?P<order>[pnum]?H?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['pH', 'nH', 'uH', 'mH', 'H']
    _dostr = 'H'
    _osuffix = 'H'


class Voltage(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>[fpnumkM]?V?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['fV', 'pV', 'nV', 'uV', 'mV', 'V', 'kV', 'MV']
    _dostr = 'V'


class VoltageAC(Voltage):
    pass


class VoltageDC(Voltage):
    pass


class DiodeVoltageDC(VoltageDC):
    pass


class Current(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>[fpnum]?A?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['fA', 'pA', 'nA', 'uA', 'mA', 'A']
    _dostr = 'A'


class CurrentAC(Current):
    pass


class CurrentDC(Current):
    pass


class Charge(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>[fpnum]?C?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['fC', 'pC', 'nC', 'uC', 'mC', 'C']
    _dostr = 'C'


class VoltageGain(GainBase):
    _regex_std = re.compile(r'^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>(V/V)?(dB)?)(?P<residual>)$')  # noqa
    _gtype = (Voltage, Voltage)
    _orders = [('', 1), ('V/V', 1), ('dB', lambda x: 10 ** (x/20))]
    _dostr = 'V/V'


class PowerRatio(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>dBm)(?P<residual>)$")  # noqa
    _ostrs = ['dBm']
    _dostr = 'dBm'

    def __repr__(self):
        return str(self._value) + self._dostr


class HFE(UnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[\d]+\.?[\d]*)\s?(?P<order>HFE)(?P<residual>)$")  # noqa
    _ostrs = ['HFE']
    _dostr = 'HFE'

    def __repr__(self):
        return str(self._value) + self._dostr


class Continuity(UnitBase):
    _dostr = None
    _parse_func = parse_none

    def __repr__(self):
        return str(self._value)


class DutyCycle(Percentage):
    pass
