# Copyright (C) 2015 Chintalagiri Shashank
# 
# This file is part of Koala.
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
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.utils.types.time import timestamp_factory
from koala.utils.types.time import TimeStamp
from koala.utils.types.time import TimeDelta


class SignalBase(object):
    def __init__(self, unitclass):
        self._unitclass = unitclass


class SignalErrorBar(object):
    def __init__(self, quantization=None, noise_floor=None, error_pc=None):
        self.quantization = quantization
        self.noise_floor = noise_floor
        self.error_pc = error_pc


class SignalPoint(SignalBase):
    def __init__(self, unitclass, value, ts=None):
        super(SignalPoint, self).__init__(unitclass)

        if not isinstance(value, unitclass):
            self.value = unitclass(value)
        else:
            self.value = value

        if ts is None:
            self.timestamp = timestamp_factory.utcnow()
        else:
            self.timestamp = ts

        self._error_bar = None

    @property
    def error_bar(self):
        return self._error_bar

    @error_bar.setter
    def error_bar(self, value):
        self._error_bar = value


class SignalWave(SignalBase):
    def __init__(self, unitclass, points=None, spacing=None, ts0=None, interpolation="piecewise_linear"):
        super(SignalWave, self).__init__(unitclass)

        if spacing is not None:
            if not isinstance(spacing, TimeDelta):
                raise TypeError("spacing must be an instance of TimeDelta")
            self._spacing = spacing

        if ts0 is not None:
            if not isinstance(ts0, TimeStamp):
                raise TypeError("ts0 must be an instance of TimeStamp")
            self._ts0 = ts0
        else:
            self._ts0 = timestamp_factory.utcnow()

        if points and isinstance(points, list):
            if isinstance(points[0], tuple):
                self._points = points
            else:
                self._points = [(ts0 + idx*spacing, point) for idx, point in enumerate(points)]

        self._interpolation = interpolation

    @property
    def last_timestamp(self):
        return self.points[-1][0]

    @property
    def points(self):
        return sorted(self._points, key=lambda x: x[0])

    def add_point(self, point, ts=None):
        if ts is None:
            ts = self.last_timestamp + self._spacing
        elif point.timestamp is not None:
            ts = point.timestamp
        self.points.append((ts, point))
