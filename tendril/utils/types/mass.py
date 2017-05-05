#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2017 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for mass
"""

import re
from unitbase import NumericalUnitBase


class Mass(NumericalUnitBase):
    _regex_std = re.compile(r"^(?P<numerical>[-+]?[\d]+\.?[\d]*)\s?(?P<order>[numk]?g?)(?P<residual>[\d]*)$")  # noqa
    _ostrs = ['ng', 'ug', 'mg', 'g', 'kg']
    _dostr = 'g'
