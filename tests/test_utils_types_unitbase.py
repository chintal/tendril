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
Docstring for test_utils_types_currency
"""

import pytest
from tendril.utils.types import unitbase
from decimal import Decimal


def test_round_to_n():
    assert unitbase.round_to_n(3.14159, 1) == 3
    assert unitbase.round_to_n(3.14159, 2) == 3.1
    assert unitbase.round_to_n(3.14159, 3) == 3.14
    assert unitbase.round_to_n(3.14159, 4) == 3.142

    assert unitbase.round_to_n(31.4159, 1) == 30
    assert unitbase.round_to_n(31.4159, 2) == 31
    assert unitbase.round_to_n(31.4159, 3) == 31.4
    assert unitbase.round_to_n(31.4159, 4) == 31.42

    assert unitbase.round_to_n(0, 1) == 0


def test_comparison_base():
    class TestType(unitbase.TypedComparisonMixin):
        def __init__(self, value):
            self.value = value

        def _cmpkey(self):
            return self.value

    class AnotherTestType(unitbase.TypedComparisonMixin):
        def __init__(self, value):
            self.value = value

        def _cmpkey(self):
            return self.value

    class BadTestType(unitbase.TypedComparisonMixin):
        def __init__(self, value):
            self.value = value

    class AnotherBadTestType(unitbase.TypedComparisonMixin):
        def __init__(self, value):
            self.value = value

        def _cmpkey(self):
            return str(self.value)

    u1 = TestType(1)
    u2 = TestType(2)
    u3 = TestType(3)
    u4 = TestType(-3)
    u5 = TestType(3)
    u6 = TestType(0)

    assert u5 == u3
    assert u1 < u2
    assert u1 <= u2
    assert u3 >= u2
    assert u3 > u2
    assert u4 < 0
    assert u5 > 0
    assert u6 == 0

    au1 = AnotherTestType(1)

    with pytest.raises(TypeError):
        au1 > u1

    with pytest.raises(TypeError):
        au1 >= u1

    with pytest.raises(TypeError):
        au1 < u1

    with pytest.raises(TypeError):
        au1 <= u1

    with pytest.raises(TypeError):
        au1 == u1

    with pytest.raises(TypeError):
        au1 != u1

    bu1 = BadTestType(10)
    bu2 = BadTestType(10)

    with pytest.raises(NotImplementedError):
        bu1 > bu2

    with pytest.raises(NotImplementedError):
        bu1 >= bu2

    with pytest.raises(NotImplementedError):
        bu1 < bu2

    with pytest.raises(NotImplementedError):
        bu1 <= bu2

    with pytest.raises(NotImplementedError):
        bu1 == bu2

    with pytest.raises(NotImplementedError):
        bu1 != bu2

    abu1 = AnotherBadTestType(10)

    with pytest.raises(TypeError):
        abu1 != u1


def test_dummyunit():
    d1 = unitbase.DummyUnit()
    d2 = unitbase.DummyUnit(value=10)

    assert repr(d1) == 'Dummy Unit'

    with pytest.raises(NotImplementedError):
        d1 + d2

    with pytest.raises(NotImplementedError):
        d1 + 0

    with pytest.raises(NotImplementedError):
        0 + d1

    with pytest.raises(NotImplementedError):
        d1 - d2

    with pytest.raises(NotImplementedError):
        d1 - 0

    # TODO Figure this out
    # with pytest.raises(NotImplementedError):
    #     0 - d1

    with pytest.raises(NotImplementedError):
        d1 * 10

    with pytest.raises(NotImplementedError):
        10 * d1

    with pytest.raises((NotImplementedError, TypeError)):
        d1 / 10

    # TODO Figure this out
    # with pytest.raises(NotImplementedError):
    #     10 / d1

    with pytest.raises((TypeError, NotImplementedError)):
        d1 > d2

    with pytest.raises((TypeError, NotImplementedError)):
        d1 < d2

    with pytest.raises((TypeError, NotImplementedError)):
        d1 > 0

    with pytest.raises((TypeError, NotImplementedError)):
        d1 < 0

    # TODO work out py3 behavior
    # with pytest.raises(NotImplementedError):
    #     d1 == d2
    #
    # with pytest.raises(NotImplementedError):
    #     d1 == 0


def test_parser_none():
    assert unitbase.parse_none(10) == 10
    assert unitbase.parse_none('10') == '10'


def test_parser_percentage():
    assert unitbase.parse_percent('10') == Decimal('10')
    assert unitbase.parse_percent('10.99') == Decimal('10.99')

    assert unitbase.parse_percent('10%') == Decimal('10')
    assert unitbase.parse_percent('10 %') == Decimal('10')
    assert unitbase.parse_percent('10.99%') == Decimal('10.99')
    assert unitbase.parse_percent('10.99 %') == Decimal('10.99')

    assert unitbase.parse_percent('10pc') == Decimal('10')
    assert unitbase.parse_percent('10 pc') == Decimal('10')
    assert unitbase.parse_percent('10.99pc') == Decimal('10.99')
    assert unitbase.parse_percent('10.99 pc') == Decimal('10.99')


def test_type_percentage():
    p1 = unitbase.Percentage(10)
    assert p1.value == Decimal('10')

    p2 = unitbase.Percentage('10')
    assert p2.value == Decimal('10')

    p3 = unitbase.Percentage('10%')
    assert p3.value == Decimal('10')


def test_type_gainbase():
    g1 = unitbase.GainBase(10, None, None, None, gtype=str)
    assert g1.in_db() == 20
    assert g1._gtype == str

    g1 = unitbase.GainBase(0.1, None, None, None, gtype=str)
    assert g1.in_db() == -20

    g1 = unitbase.GainBase(100, None, None, None, gtype=str)
    assert g1.in_db() == 40
