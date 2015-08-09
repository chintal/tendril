#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of koala.
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
Docstring for measurements
"""

from koala.utils import log
logger = log.get_logger(__name__, log.INFO)

import time
import arrow

from koala.utils.types.electromagnetic import Voltage
from koala.testing.testbase import TestMeasurementBase
from koala.testing.testbase import TestSimpleMeasurement


class DCVoltageMeasurement(TestSimpleMeasurement):
    def __init__(self):
        super(DCVoltageMeasurement, self).__init__()
        self._outputchannel = None
        self._inputtype = None
        self._inputchannel = None

    def do_measurement(self):
        """
        This function is present only because the instrument return value is not of a
        SignalPoint Type. Instrument classes should be changed to use Signal Point type
        instead and this class should fall back to the parent's implementation.
        """
        logger.debug("Making measurement : " + repr(self))
        if self._output is not None:
            if self._outputchannel is None:
                raise IOError("Output channel is not defined")
            self._outputchannel.set(self._output)

        if self.stime is not None:
            time.sleep(self.stime)

        if self._inputtype is not None:
            if self._inputchannel is None:
                raise IOError("Input channel is not defined")
            self._input = self._inputchannel.get()
            # if self._input.unitclass and not self._input.unitclass == self._inputtype:
            #     raise TypeError("Expected " + self._inputtype.unitclass + ", got " + type(self._input))

        self._ts = arrow.utcnow()

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value
        self._inputtype = Voltage
        self._inputchannel = self._parent.instrument.voltage_input

    @property
    def input_voltage(self):
        return self._input

    def yesorno(self):
        pass

    def render(self):
        return {
            'input': {'v': repr(self._input)},
            'timestamp': self._ts.isoformat()
            }


class TestUserMeasurement(TestMeasurementBase):
    def __init__(self, string):
        super(TestUserMeasurement, self).__init__()
        self._string = string
        self._user_input = None

    def do_measurement(self):
        while self.input_valid is False:
            self._user_input = raw_input(self._string + ' [y/n] : ').strip()
        self._ts = arrow.utcnow()

    @property
    def input_valid(self):
        if self._user_input is None:
            return False
        if self._user_input.lower() in ['y', 'yes', 'ok', 'pass', 'n', 'no', 'fail']:
            return True
        else:
            return False

    @property
    def yesorno(self):
        if self._user_input.lower() in ['y', 'yes', 'ok', 'pass']:
            return True
        else:
            return False

    def render(self):
        return {'question': self._string + ' [y/n] : ' + str(self.yesorno),
                'timestamp': self._ts.isoformat()}
