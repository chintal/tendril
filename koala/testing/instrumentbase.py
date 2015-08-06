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


class InstrumentChannelBase(object):
    def __init__(self, parent):
        self._parent = parent


class InstrumentInputChannelBase(InstrumentChannelBase):
    def __init__(self, parent):
        super(InstrumentInputChannelBase, self).__init__(parent)

    def get(self):
        raise NotImplementedError


class InstrumentOutputChannelBase(InstrumentChannelBase):
    def __init__(self, parent):
        super(InstrumentOutputChannelBase, self).__init__(parent)

    def set(self, signal):
        raise NotImplementedError


class InstrumentBase(object):
    def __init__(self, channels=None):
        self._ident = None
        self._channels = channels
        self._configurations = []

    def _detect(self):
        raise NotImplementedError

    def configure(self, configuration):
        raise NotImplementedError

    @property
    def configurations(self):
        return self._configurations

    @property
    def channels(self):
        return self._channels

    @property
    def ident(self):
        return self._ident
