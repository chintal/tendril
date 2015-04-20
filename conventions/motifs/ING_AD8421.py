"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from ingbase import MotifInampGainBase


class MotifING_AD8421(MotifInampGainBase):
    def res_to_gain(self, res):
        if res is None:
            return 1
        return 1 + (9900 / res)

    def gain_to_res(self, gain):
        if gain is 1:
            return None
        if gain < 1:
            raise ValueError
        return 9900.0 / (gain - 1)
