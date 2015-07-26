"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
from utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from decimal import Decimal
import numbers
import re

lrex = re.compile(ur'^((?P<m>[-+]?\d*\.*\d+) *(m|mtr) *$)|((?P<um>[-+]?\d*\.*\d+) *um *$)|((?P<cm>[-+]?\d*\.*\d+) *cm *$)|((?P<mm>[-+]?\d*\.*\d+) *mm *$)|((?P<mil>[-+]?\d*\.*\d+) *mil *$)|((?P<cmil>[-+]?\d*\.*\d+) *cmil *$)|((?P<in>[-+]?\d*\.*\d+) *(in|inch) *$)',
                  re.IGNORECASE)


class Length(object):
    def __init__(self, lstr=None, length=None, defunit='mm'):
        self._lstr = None
        self._olength = None
        self._ounit = None
        if lstr is not None:
            try:
                float(lstr)
                lstr += defunit
            except ValueError:
                pass
            self._lstr = lstr
        elif length is not None and defunit is not None:
            self._lstr = str(length) + defunit
        self._parse_length()

    def _parse_length(self):
        match = lrex.match(self._lstr)
        if match is None:
            logger.warning("Length not parsed : " + self._lstr)
            self._olength = 0
            self._ounit = 'mm'
            raise ValueError(self._lstr)

        mm = match.group('um')
        if mm is not None:
            self._olength = Decimal(mm)
            self._ounit = 'um'
            return

        mm = match.group('mm')
        if mm is not None:
            self._olength = Decimal(mm)
            self._ounit = 'mm'
            return

        cm = match.group('cm')
        if cm is not None:
            self._olength = Decimal(cm)
            self._ounit = 'cm'

        m = match.group('m')
        if m is not None:
            self._olength = Decimal(m)
            self._ounit = 'm'

        inch = match.group('in')
        if inch is not None:
            self._olength = Decimal(inch)
            self._ounit = 'in'

        mil = match.group('mil')
        if mil is not None:
            self._olength = Decimal(mil)
            self._ounit = 'mil'

        cmil = match.group('cmil')
        if cmil is not None:
            self._olength = Decimal(cmil)
            self._ounit = 'cmil'

    def __repr__(self):
        if self.__float__() < 10:
            return str(round(self.__float__(), 2)) + " mm"
        elif self.__float__() < 1000:
            return str(round(self.__float__() / 10, 2)) + " cm"
        else:
            return str(round(self.__float__() / 1000, 2)) + " m"

    def __float__(self):
        return float(self._length)

    @property
    def decimal(self):
        return self._length

    @property
    def _length(self):
        if self._ounit == 'um':
            return self._olength / 1000
        elif self._ounit == 'mm':
            return self._olength
        elif self._ounit == 'cm':
            return self._olength * 10
        elif self._ounit == 'm':
            return self._olength * 1000
        elif self._ounit == 'in':
            return self._olength * Decimal(25.4)
        elif self._ounit == 'mil':
            return self._olength * Decimal(25.4) / 1000
        elif self._ounit == 'cmil':
            return self._olength * Decimal(25.4) / 100000

    @property
    def lstr(self):
        return self._lstr

    def __add__(self, other):
        return Length(length=self._length + float(other))

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, numbers.Number):
            return Length(length=self._length * other)
        else:
            raise TypeError

    def __div__(self, other):
        if isinstance(other, numbers.Number):
            return Length(length=self._length / other)
        elif isinstance(other, Length):
            return self._length / float(other)
        else:
            raise TypeError

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other.__mul__(-1))

    def __cmp__(self, other):
        if self._length == float(other):
            return 0
        elif self._length < float(other):
            return -1
        else:
            return 1
