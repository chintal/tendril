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
Docstring for test_utils_types_cartesian
"""

from tendril.utils.types import cartesian
import pytest


def test_cartesian():
    p1 = cartesian.CartesianPoint(1, 1)
    p2 = cartesian.CartesianPoint(10, 10)
    p3 = cartesian.CartesianPoint(1, 1)
    p4 = cartesian.CartesianPoint(2, 2)
    p5 = cartesian.CartesianPoint(12, 12)
    p6 = cartesian.CartesianPoint(-1, -1)
    p7 = cartesian.CartesianPoint(2, -1)
    p8 = cartesian.CartesianPoint(0, 0)
    p9 = cartesian.CartesianPoint(3, 4)

    assert p1 != p2
    assert p1 == p3

    l1 = cartesian.CartesianLineSegment(p1, p2)

    assert l1.x(0) == p1.x
    assert l1.y(0) == p1.y
    assert l1.x(1) == p2.x
    assert l1.y(1) == p2.y

    assert p4 in l1
    assert p5 not in l1
    assert p6 not in l1
    assert p7 not in l1

    l2 = cartesian.CartesianLineSegment(p8, p9)

    assert repr(l2.length()) == '5.0mm'

    with pytest.raises(Exception):
        cartesian.CartesianLineSegment(p1, p3)

    # TODO Allow this with proper lengths support
    p10 = cartesian.CartesianPoint(4, 6)
    p10.unit = 'cm'
    with pytest.raises(ValueError):
        cartesian.CartesianLineSegment(p1, p10)

    p11 = cartesian.CartesianPoint(1, 10)
    l3 = cartesian.CartesianLineSegment(p1, p11)
    assert cartesian.CartesianPoint(1, 2) in l3
    assert cartesian.CartesianPoint(2, 1) not in l3
    with pytest.raises(ZeroDivisionError):
        l3.t_x(1)
    with pytest.raises(ZeroDivisionError):
        l3.t_x(2)

    p12 = cartesian.CartesianPoint(10, 1)
    l4 = cartesian.CartesianLineSegment(p1, p12)
    assert cartesian.CartesianPoint(2, 1) in l4
    assert cartesian.CartesianPoint(1, 2) not in l4
    with pytest.raises(ZeroDivisionError):
        l4.t_y(1)
    with pytest.raises(ZeroDivisionError):
        l4.t_y(2)
