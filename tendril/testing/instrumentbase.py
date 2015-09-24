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


class InstrumentChannelBase(object):
    def __init__(self, parent):
        self._parent = parent

    @property
    def is_enabled(self):
        if self in self._parent.channels:
            return True
        else:
            return False


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


class SignalWaveInputChannel(InstrumentInputChannelBase):
    """
    This class provides the bulk of the accessors to the instrument
    channels providing vanilla SignalWave types. More complex implementations
    should provide their own channel classes.

    :param parent: The instrument of which this channel is a part of.
    :param interface: The interface to the instrument.
    :param chidx: The channel index.

    """
    def __init__(self, parent, interface, chidx):
        super(SignalWaveInputChannel, self).__init__(parent)
        self._interface = interface
        self._chidx = chidx

    def get(self, unitclass=None, flush=True):
        """
        Gets the latest data point in the channel's point buffer. By default,
        it also flushes any older points from the buffer. This behavior can be
        suppressed by passing flush=False.

        :param unitclass: Unit class of which the data point is expected, or
                          None if you don't care.
        :param flush: Whether or not older points should be flushed.
                      Default True.
        :return: Latest datapoint.
        :rtype: :class:`tendril.utils.types.signalbase.SignalPoint`

        """
        value = self._interface.latest_point(chidx=self._chidx, flush=flush)
        if unitclass is None or value.unitclass == unitclass:
            return value
        else:
            raise TypeError

    def get_next_chunk(self, unitclass=None, maxlen=None):
        """
        Gets the next chunk of data from the instrument channel. Note that the
        chunk returned has already been removed from the channel's
        point buffer.

        :param unitclass: Unit class of which the data point is expected, or
                          None if you don't care.
        :return: Wave containing all but the latest data point in the
                 channel's point buffer.
        :rtype: :class:`tendril.utils.types.signalbase.SignalWave`

        """
        chunk = self._interface.next_chunk(chidx=self._chidx)
        if unitclass is None or chunk.unitclass == unitclass:
            if maxlen is not None:
                if maxlen > chunk.maxlen:
                    chunk.maxlen = maxlen
                return chunk
            else:
                return chunk
        else:
            raise TypeError

    def reset_wave(self):
        """
        Resets the point / wave buffer in the channel
        """
        self._interface.reset_buffer(chidx=self._chidx)

    @property
    def data_available(self):
        return self._interface.data_available(chidx=self._chidx)


class InstrumentBase(object):
    def __init__(self, channels=None):
        self._ident = None
        self._sno = None
        self._channels = channels
        self._configurations = []

        self._connected = None
        self._consumers = []

    def consumer_register(self, consumer):
        if self._connected is not True:
            try:
                self.connect()
            except NotImplementedError:
                pass
        self._consumers.append(consumer)

    def consumer_done(self, consumer):
        self._consumers.remove(consumer)
        if len(self._consumers) == 0 and self._connected is True:
            try:
                self.disconnect()
            except NotImplementedError:
                pass

    @property
    def connected(self):
        return self._connected

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

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
        if self._sno is not None:
            return str(self._ident) + ' ' + str(self._sno)
        else:
            return self._ident
