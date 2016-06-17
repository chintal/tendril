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

from ingbase import MotifInampGainBase
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import VoltageGain


class MotifING_AD8223(MotifInampGainBase):
    def res_to_gain(self, res):
        if res is None:
            return VoltageGain(1)
        if isinstance(res, str):
            res = Resistance(res)
        if isinstance(res, Resistance):
            res = float(res)
        return VoltageGain(5 + (80000.0 / res))

    def gain_to_res(self, gain):
        if isinstance(gain, str):
            gain = VoltageGain(gain)
        if isinstance(gain, VoltageGain):
            gain = float(gain)
        if gain is 1:
            return None
        if gain < 1:
            raise ValueError
        return Resistance(80000.0 / (gain - 5))
