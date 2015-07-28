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
    def __init__(self, channels):
        self._channels = channels
        self._configurations = []

    def _detect(self):
        raise NotImplementedError

    def configure(self, configuration):
        raise NotImplementedError

    @property
    def configurations(self):
        return self._configurations
