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
Docstring for test_utils_types_times
"""

from tendril.utils.types import time
from decimal import Decimal
import pytest


def test_parser_frequency():
    assert time.parse_frequency('10Hz') == Decimal('10')
    assert time.parse_frequency('10.22Hz') == Decimal('10.22')
    assert time.parse_frequency('10.00Hz') == Decimal('10.00')
    assert time.parse_frequency('10kHz') == Decimal('10000')
    assert time.parse_frequency('10.2kHz') == Decimal('10200')
    assert time.parse_frequency('10.2MHz') == Decimal('10200000')
    assert time.parse_frequency('102MHz') == Decimal('102000000')
    assert time.parse_frequency('2GHz') == Decimal('2000000000')
    assert time.parse_frequency('2.1GHz') == Decimal('2100000000')
    assert time.parse_frequency('10mHz') == Decimal('0.01')
    assert time.parse_frequency('10.5mHz') == Decimal('0.0105')
    with pytest.raises(ValueError):
        assert time.parse_frequency('10.5') == Decimal('0.0105')


def test_type_frequency():
    f1 = time.Frequency('10Hz')

    tp1 = 1 / f1
    assert isinstance(tp1, time.TimeSpan)
    assert tp1.timedelta.microseconds == 100000

    tp1 = 10 / f1
    assert isinstance(tp1, time.TimeSpan)
    assert tp1.timedelta.seconds == 1

    f2 = f1 / 10
    assert isinstance(f2, time.Frequency)
    assert f2.value == 1


def test_type_timespan():

    ts1 = time.TimeSpan(10)
    assert ts1.timedelta.seconds == 10
    assert repr(ts1) == '0:0:0:0:0:10:0'

    ts1 = time.TimeSpan(0.1)
    assert ts1.timedelta.microseconds == 100000

    ts1 = time.TimeSpan(3610)
    assert ts1.timedelta.seconds == 3610

    ts1 = time.TimeSpan(time.TimeDelta(
        days=1, hours=1, minutes=1, seconds=1, microseconds=1
    ))
    assert ts1.timedelta.seconds == 90061
    assert ts1.timedelta.microseconds == 1

    with pytest.raises(ValueError):
        time.TimeSpan(time.TimeDelta(years=1))

    with pytest.raises(ValueError):
        time.TimeSpan(time.TimeDelta(months=1))

    with pytest.raises(TypeError):
        time.TimeSpan('100')

    # TODO Test arithmetic


def test_time_factory():
    pass
