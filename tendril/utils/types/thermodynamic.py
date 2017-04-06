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


import re
from decimal import Decimal as D
from .unitbase import NumericalUnitBase


class Temperature(NumericalUnitBase):
    _regex_std = re.compile(r'^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>(mK)?[CFK]?)(?P<residual>)$')  # noqa
    _orders = [('C', lambda x: x + D('273.14')),
               ('F', lambda x: ((x - D('32')) * D('5')) / D('9') + D('273.14')),
               ('K', 1),
               ('mK', D('0.001'))]
    _dostr = 'K'
    _allow_nOr = False

    def __repr__(self):
        return str(self._value) + self._dostr


class ThermalDissipation(NumericalUnitBase):
    _regex_std = re.compile(r'^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>[numkM]?W)(?P<residual>)$')  # noqa
    _ostrs = ['nW', 'uW', 'mW', 'W', 'kW', 'MW']
    _dostr = 'W'
    _allow_nOr = False
