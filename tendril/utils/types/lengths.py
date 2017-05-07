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

import re
from decimal import Decimal
from tendril.utils import log
from .unitbase import NumericalUnitBase

logger = log.get_logger(__name__, log.DEFAULT)


lrex = re.compile(r'^((?P<m>[-+]?\d*\.*\d+) *(m|mtr|meter|metre) *$)|((?P<um>[-+]?\d*\.*\d+) *um *$)|((?P<cm>[-+]?\d*\.*\d+) *cm *$)|((?P<mm>[-+]?\d*\.*\d+) *mm *$)|((?P<mil>[-+]?\d*\.*\d+) *mil *$)|((?P<cmil>[-+]?\d*\.*\d+) *cmil *$)|((?P<in>[-+]?\d*\.*\d+) *(in|inch|Inch) *$)|((?P<feet>[-+]?\d*\.*\d+) *(ft|feet|Feet) *$)',  # noqa
                  re.IGNORECASE)


def parse_length(value):
    match = lrex.match(value)
    if match is None:
        logger.warning("Length not parsed : " + value)
        raise ValueError(value)

    um = match.group('um')
    if um is not None:
        _olength = Decimal(um) / Decimal('1000000')
        return _olength

    mm = match.group('mm')
    if mm is not None:
        _olength = Decimal(mm) / Decimal('1000')
        return _olength

    cm = match.group('cm')
    if cm is not None:
        _olength = Decimal(cm) / Decimal('100')
        return _olength

    m = match.group('m')
    if m is not None:
        _olength = Decimal(m)
        return _olength

    inch = match.group('in')
    if inch is not None:
        _olength = Decimal(inch) * Decimal('25.4') / Decimal('1000')
        return _olength

    feet = match.group('feet')
    if feet is not None:
        _olength = Decimal(feet) * 12 * Decimal('25.4') / Decimal('1000')
        return _olength

    mil = match.group('mil')
    if mil is not None:
        _olength = Decimal(mil) * Decimal('25.4') / Decimal('1000000')
        return _olength

    cmil = match.group('cmil')
    if cmil is not None:
        _olength = Decimal(cmil) * Decimal('25.4') / Decimal('100000')
        return _olength


class Length(NumericalUnitBase):
    _ostrs = ['um', 'mm', 'm', 'km']
    _dostr = 'm'
    _parse_func = staticmethod(parse_length)
