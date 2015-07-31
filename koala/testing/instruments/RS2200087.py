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


from koala.utils import log
logger = log.get_logger(__name__, log.DEBUG)

import re

from driver2200087.runner import InstProtocol2200087
from driver2200087.runner import InstInterface2200087
from driver2200087.runner import InstFactory2200087

from koala.utils.types.signalbase import SignalPoint
from koala.utils.types.signalbase import SignalWave

from koala.utils.types.time import TimeDelta
from koala.utils.types.time import timestamp_factory

from koala.utils.types import electromagnetic
from koala.utils.types import thermodynamic
from koala.utils.types.time import Frequency
from koala.utils.types.time import TimeSpan
from koala.utils.types.unitbase import DummyUnit

from koala.testing.instrumentbase import InstrumentBase
from koala.testing.instrumentbase import InstrumentInputChannelBase

from decimal import Decimal
from decimal import InvalidOperation


def voltage_processor(m):
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = ''
    rval = num + rng + 'V'
    return rval


def resistance_processor(m):
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng is None:
            rng = ''
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = 'E'
    rval = num + rng
    return rval


def capacitance_processor(m):
    num = m.group('number')
    rng = m.group('range')
    if rng is None:
        rng = ''
    rval = num + rng + 'F'
    return rval


def frequency_processor(m):
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng is None:
            rng = ''
    except IndexError:
        rng = ''
    rval = num + rng + 'Hz'
    return rval


def time_processor(m):
    num = Decimal(m.group('number'))
    try:
        rng = m.group('range')
        if rng is None:
            rng = 1
        elif rng == 'm':
            rng = Decimal(1)/1000
        elif rng == 'u':
            rng = Decimal(1)/1000000
        elif rng == 'n':
            rng = Decimal(1)/1000000000
    except IndexError:
        rng = 1
    rval = num * rng
    return rval


def current_processor(m):
    num = m.group('number')
    try:
        rng = m.group('range')
        if rng == 'K':
            rng = 'k'
    except IndexError:
        rng = ''
    rval = num + rng + 'A'
    return rval


def power_processor(m):
    return m.group('number') + 'dBm'


def hfe_processor(m):
    return m.group('number') + 'HFE'


def duty_processor(m):
    return m.group('number') + '%'


def continuity_processor(m):
    rval = 'CLOSED'
    if m.group('string') == '0PEN':
        rval = 'OPEN'
    return rval


rex_list = [(thermodynamic.Temperature,
             re.compile(ur'^(?P<string>[-?[0-9\\.]+[CFK])(?P<HOLD> HOLD)?$'),
             None),
            (electromagnetic.VoltageDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? VOLTS$'),
             voltage_processor),
            (electromagnetic.VoltageAC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) AC(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? VOLTS$'),
             voltage_processor),
            (electromagnetic.CurrentDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? AMPS$'),
             current_processor),
            (electromagnetic.CurrentAC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) AC(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? AMPS$'),
             current_processor),
            (electromagnetic.Continuity,
             re.compile(ur'^(?P<string>0PEN) CONTINUITY(?P<HOLD> HOLD)?$'),
             continuity_processor),
            (electromagnetic.DiodeVoltageDC,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+) DIODE(?P<HOLD> HOLD)? VOLTS$'),
             voltage_processor),
            (electromagnetic.Resistance,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? OHMS$'),
             resistance_processor),
            (electromagnetic.Capacitance,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)?( (?P<range>[munKM]) \(1e(?P<power>-?[\d]+)\))? FARADS$'),
             capacitance_processor),
            (Frequency,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)? Hz$'),
             frequency_processor),
            (electromagnetic.PowerRatio,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<HOLD> HOLD)? dBm$'),
             power_processor),
            (electromagnetic.DutyCycle,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)(?P<HOLD> HOLD)? Percent$'),
             duty_processor),
            (TimeSpan,
             re.compile(ur'^(?P<number>[-?[0-9\\.]+)(?P<AUTO> AUTO)?(?P<HOLD> HOLD)? SECONDS( (?P<range>[mun]) \(1e(?P<power>-?[\d]+)\))?$'),
             time_processor),
            ]

# TODO Handle closed continuty
# TODO Handle open diode
# TODO Handle open resistor
# TODO Handle shorted capacitor
# TODO Handle Logic


class KoalaProtocol2200087(InstProtocol2200087):
    def __init__(self, port, buffer_size):
        InstProtocol2200087.__init__(self, port=port, buffer_size=buffer_size)
        self.reset_buffer(DummyUnit)

    def reset_buffer(self, unitclass):
        # logger.debug("Resetting buffer to type : " + repr(unitclass))
        print "Resetting buffer to type : " + repr(unitclass)
        self.point_buffer = SignalWave(unitclass,
                                       spacing=TimeDelta(microseconds=100000),
                                       ts0=timestamp_factory.now(),
                                       buffer_size=1000,
                                       use_point_ts=False)

    @staticmethod
    def _get_point(string):
        if string is None:
            return SignalPoint(DummyUnit, None)
        for rex in rex_list:
            m = rex[1].match(string.strip())
            if m is not None:
                if rex[2] is not None:
                    rstring = rex[2](m)
                else:
                    rstring = m.group('string')
                try:
                    return SignalPoint(rex[0], rstring)
                except (InvalidOperation, ValueError):
                    logger.error("Unable to make unit from string : " + rstring + " : " + repr(rex[0]))
                    return SignalPoint(rex[0], 0)
        raise ValueError("String not recognized : " + string)

    def frame_received(self, frame):
        frame = [byte.encode('hex') for byte in frame]
        chunk = ' '.join(frame)
        string = self._frame_processor(chunk)
        point = self._get_point(string)
        if not point.unitclass == self.point_buffer.unitclass:
            self.reset_buffer(point.unitclass)
        self.point_buffer.add_point(point)


class KoalaFactory2200087(InstFactory2200087):
    """
    This factory produces protocols integrated with Koala unit classes, and
    it's instance in this module can be used to modify the Instrument
    Interfaces to produce Koala SignalPoints and SignalWaves instead of
    strings.

    See the InstFactory2200087 documentation for more detailed information.
    """
    def buildProtocol(self, port='/dev/ttyUSB0', buffer_size=100):
        """
        This function returns a KoalaProtocol2200087 instance, bound to the
        port specified by the param port.

        :param port: Serial port identifier to which the device is connected
        :type port: str

        """
        instance = KoalaProtocol2200087(port=port, buffer_size=buffer_size)
        return instance

factory = KoalaFactory2200087()


class DMMInputChannel(InstrumentInputChannelBase):
    def __init__(self, parent, interface):
        super(DMMInputChannel, self).__init__(parent)
        self._interface = interface

    def get(self, unitclass=None):
        value = self._interface.latest_point()
        if unitclass is not None:
            if isinstance(value, unitclass):
                return value
            else:
                raise TypeError
        return value

    def get_wave(self, unitclass=None):
        pass

    def reset_wave(self):
        pass


class InstrumentRS2200087(InstrumentBase):
    def __init__(self, channels=None):
        super(InstrumentRS2200087, self).__init__(channels)
        self._detect()

    def _detect(self):
        self._dmm = InstInterface2200087(pfactory=factory)
        self._dmm.connect()
        self._channels = DMMInputChannel(self, self._dmm)

    def configure(self, configuration):
        raise NotImplementedError


if __name__ == "__main__":
    i = InstrumentRS2200087()
