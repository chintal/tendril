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
from tendril.utils.types.unitbase import Percentage
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

    tp2 = Percentage(50) / f1
    assert isinstance(tp2, time.TimeSpan)
    assert tp2.timedelta.microseconds == 50000


def test_parser_timespan():
    assert time.parse_time('10s') == Decimal('10')
    assert time.parse_time('10.2s') == Decimal('10.2')
    assert time.parse_time('10ms') == Decimal('0.010')
    assert time.parse_time('10.2ms') == Decimal('0.0102')
    assert time.parse_time('10us') == Decimal('0.000010')
    assert time.parse_time('10.2us') == Decimal('0.0000102')
    assert time.parse_time('10ns') == Decimal('0.000000010')
    assert time.parse_time('10.2ns') == Decimal('0.0000000102')
    assert time.parse_time('10ps') == Decimal('0.000000000010')
    assert time.parse_time('10.2ps') == Decimal('0.0000000000102')
    assert time.parse_time('10fs') == Decimal('0.000000000000010')
    assert time.parse_time('10.2fs') == Decimal('0.0000000000000102')
    with pytest.raises(ValueError):
        assert time.parse_time('10.5') == Decimal('0.0105')


def test_type_timespan():

    ts1 = time.TimeSpan(10)
    assert ts1.timedelta.seconds == 10
    assert repr(ts1) == '10s'

    ts1 = time.TimeSpan(Decimal('0.1'))
    assert ts1.timedelta.microseconds == 100000
    assert repr(ts1) == '100.0ms'

    ts1 = time.TimeSpan(3610)
    assert ts1.timedelta.seconds == 3610
    assert repr(ts1) == repr(ts1.timedelta)

    ts1 = time.TimeSpan(time.TimeDelta(
        days=1, hours=1, minutes=1, seconds=1, microseconds=1
    ))
    assert ts1.timedelta.seconds == 90061
    assert ts1.timedelta.microseconds == 1

    with pytest.raises(ValueError):
        time.TimeSpan(time.TimeDelta(years=1))

    with pytest.raises(ValueError):
        time.TimeSpan(time.TimeDelta(months=1))

    with pytest.raises(ValueError):
        time.TimeSpan('100')

    ts1 = time.TimeSpan(Decimal('0.1'))
    f1 = 1 / ts1
    assert isinstance(f1, time.Frequency)
    assert f1.value == Decimal('10')

    f1 = Percentage(50) / ts1
    assert isinstance(f1, time.Frequency)
    assert f1.value == Decimal('5')


def test_time_factory():
    pass
