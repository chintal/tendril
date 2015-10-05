#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for test_utils_types_thermodynamic.py
"""

from tendril.utils.types import thermodynamic
import pytest
from decimal import Decimal


def test_parser_temperature():
    assert thermodynamic.parse_temperature('0C') == Decimal('273.14')
    assert thermodynamic.parse_temperature('100C') == Decimal('373.14')
    assert thermodynamic.parse_temperature('0 C') == Decimal('273.14')
    assert thermodynamic.parse_temperature('100 C') == Decimal('373.14')
    assert thermodynamic.parse_temperature('273.14K') == Decimal('273.14')
    assert thermodynamic.parse_temperature('373.14K') == Decimal('373.14')
    assert thermodynamic.parse_temperature('273.14 K') == Decimal('273.14')
    assert thermodynamic.parse_temperature('373.14 K') == Decimal('373.14')
    assert thermodynamic.parse_temperature('32F') == Decimal('273.14')
    assert thermodynamic.parse_temperature('212F') == Decimal('373.14')
    assert thermodynamic.parse_temperature('32 F') == Decimal('273.14')
    assert thermodynamic.parse_temperature('212 F') == Decimal('373.14')


def test_type_temperature():
    t1 = thermodynamic.Temperature('100C')
    assert repr(t1) == '373.14K'
    t2 = thermodynamic.Temperature('373.14K')
    assert repr(t2) == '373.14K'
    t3 = thermodynamic.Temperature('212F')
    assert repr(t3) == '373.14K'
    t4 = thermodynamic.Temperature('80K')
    t5 = thermodynamic.Temperature(Decimal('373.14'))

    assert t2 == t3
    assert t5 == t2
    assert t2 != t4
    assert t2 > t4
    assert t4 < t2
    assert t4 > 0
