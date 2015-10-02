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
from numbers import Number
from tendril.utils.types import currency
from tendril.utils import config


def test_currency_definitions():
    # Test native currency and basic functions
    assert isinstance(currency.native_currency_defn, currency.CurrencyDefinition)
    assert currency.native_currency_defn.exchval == 1
    assert currency.native_currency_defn.code == config.BASE_CURRENCY
    assert currency.native_currency_defn.symbol == config.BASE_CURRENCY_SYMBOL

    # Test currency creation
    if currency.BASE_CURRENCY != 'USD':
        fcur = 'USD'
    else:
        fcur = 'GBP'
    fcd = currency.CurrencyDefinition(fcur)
    assert fcd.symbol == fcur
    assert isinstance(fcd.exchval, float)
    assert fcd.exchval != 1

    with pytest.raises(KeyError):
        currency.CurrencyDefinition('NOCURRENCYHERE')

    # Test Equality
    lcd = currency.CurrencyDefinition(config.BASE_CURRENCY, config.BASE_CURRENCY_SYMBOL)
    assert lcd == currency.native_currency_defn
    assert fcd != currency.native_currency_defn
    slcd = currency.CurrencyDefinition(config.BASE_CURRENCY, config.BASE_CURRENCY_SYMBOL, 3)
    assert lcd != slcd
    tlcd = currency.CurrencyDefinition(config.BASE_CURRENCY, "Some other Symbol", 3)
    assert tlcd != slcd


def test_currency_values():
    ncd = currency.native_currency_defn
    cv1 = currency.CurrencyValue(1, ncd)

    assert float(cv1) == 1.0
    assert repr(cv1) == config.BASE_CURRENCY_SYMBOL + '1.00'

    if currency.BASE_CURRENCY != 'USD':
        fcur = 'USD'
    else:
        fcur = 'GBP'

    fcd = currency.CurrencyDefinition(fcur, exchval=10)
    fcv1 = currency.CurrencyValue(1, fcd)
    assert fcv1.source_value == 1
    assert fcv1.native_value == 10
    assert fcv1.source_string == fcur + '1.00'
    assert fcv1.native_string == config.BASE_CURRENCY_SYMBOL + '10.00'

    fcv2 = currency.CurrencyValue(1, fcur)
    assert fcv2._currency_def._code == fcur

    cv2 = cv1 + fcv1

    assert cv2.native_value == 11
    assert cv2.source_value == 11
    assert cv2._currency_def == ncd

    cv3 = cv1 + 0
    assert cv1 == cv3

    cv3 = 0 + cv1
    assert cv1 == cv3

    cv3 = cv3 + cv1
    assert cv3.native_value == 2

    with pytest.raises(NotImplementedError):
        cv1 + 10

    with pytest.raises(NotImplementedError):
        10 + cv1

    cv3 = cv2 - cv1
    assert cv3.native_value == 10

    cv3 = cv2 - 0
    assert cv3.native_value == 11

    with pytest.raises(NotImplementedError):
        cv2 - "Test"

    # TODO Implement this?
    # cv3 = 0 - cv2
    # assert cv3.native_value == 11

    # with pytest.raises(NotImplementedError):
    #     "Test" - cv2

    cv3 = cv1 * 10
    assert cv3.native_value == 10
    assert cv3._currency_def == cv1._currency_def

    cv3 = 10 * cv1
    assert cv3.native_value == 10
    assert cv3._currency_def == cv1._currency_def

    with pytest.raises(NotImplementedError):
        cv1 * cv3

    ratio = fcv1 / cv1
    assert ratio == 10
    assert isinstance(ratio, Number)

    cv3 = cv1 / 10
    assert cv3.native_value == 1 / 10
    assert cv3._currency_def == cv1._currency_def

    with pytest.raises(NotImplementedError):
        cv1 / '10'

    assert 0 < cv1
    assert 0 == cv1 - cv1
    assert cv2 - 11 * cv1 == 0
    assert 0 > currency.CurrencyValue(-1, ncd)
    assert currency.CurrencyValue(-1, ncd) < 0
    assert cv1 > 0
    assert cv1 < cv2
    assert cv2 > cv1
    assert fcv1 == cv1 * 10

    with pytest.raises(TypeError):
        cv1 > 10
