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

from koala.utils import log
logger = log.get_logger(__name__, log.INFO)

import time
from datetime import datetime
import arrow


class TestPrepBase(object):
    """ Object representing a preparatory step for a Test """
    def __init__(self):
        self._parent = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    def run_prep(self):
        raise NotImplementedError


class TestPrepUser(TestPrepBase):
    def __init__(self, string):
        super(TestPrepUser, self).__init__()
        self._string = string

    def run_prep(self):
        print self._string
        raw_input("Press Enter to continue...")


class TestMeasurementBase(object):
    """ Object representing a single measurement for a Test """
    def __init__(self):
        self._parent = None
        self._ts = None

    def do_measurement(self):
        """
        This is the measurement function. This should be overridden
        by the actual Test classes to perform the actual measurement.
        """
        raise NotImplementedError

    def render(self):
        """
        This is an example render function. This should be overridden by the
        actual Test classes to render the actual result.

        Rendering means encoding the test result into a JSON representation,
        which can later be dumped into a postgres database.
        """
        raise NotImplementedError

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def yesorno(self):
        raise NotImplementedError


class TestUserMeasurement(TestMeasurementBase):
    def __init__(self, string):
        super(TestUserMeasurement, self).__init__()
        self._string = string
        self._user_input = None

    def do_measurement(self):
        while self.input_valid is False:
            self._user_input = raw_input(self._string).strip()
        self._ts = datetime.now()

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
        return {'question': self._string + str(self.yesorno),
                'timestamp': self._ts.isoformat()}


class TestSimpleMeasurement(TestMeasurementBase):
    def __init__(self):
        super(TestSimpleMeasurement, self).__init__()
        self._outputchannel = None
        self._output = None
        self._stime = None
        self._inputchannel = None
        self._input = None
        self._inputtype = None
        self._instrument = None

    def do_measurement(self):
        """
        This is an example measurement function. This should be overridden
        by the actual Test classes to perform the actual measurement, and
        this code can be used as a starting point.

        The result of the measurement would typically be some composition of
        instances of :class:`koala.utils.type.signalbase.SignalBase`.
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
            if self._input.unitclass and not self._input.unitclass == self._inputtype:
                raise TypeError("Expected " + self._inputtype.unitclass + ", got " + type(self._input))

        self._ts = arrow.utcnow()

    @property
    def stime(self):
        return self._stime

    @property
    def yesorno(self):
        raise NotImplementedError

    def render(self):
        return {'instrument': (self._instrument.ident if self._instrument is not None else None),
                'output': self._output,
                'input': self._input}


class RunnableTest(object):
    def __init__(self):
        self._serialno = None
        self._parent = None
        self._desc = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def serialno(self):
        if self._serialno is not None:
            return self._serialno
        else:
            return self._parent.serialno

    @serialno.setter
    def serialno(self, value):
        self._serialno = value

    def run_test(self):
        raise NotImplementedError

    @property
    def passed(self):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

    def finish(self):
        logger.info(repr(self) + " :: Result : " + str(self.passed()))

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value


class TestBase(RunnableTest):
    """ Object representing a full runnable Test of the same Measurement type"""
    def __init__(self):
        super(TestBase, self).__init__()
        self._prep = []
        self._measurements = []
        self._result = None
        self.variables = {}

    def add_measurement(self, measurement):
        measurement.parent = self
        self._measurements.append(measurement)
        return measurement

    def run_test(self):
        logger.debug("Running Test : " + repr(self))
        for prep in self._prep:
            prep.run_prep()
        for measurement in self._measurements:
            measurement.do_measurement()

    def configure(self, **kwargs):
        self.variables.update(kwargs)

    def add_prep(self, prep):
        prep.parent = self
        self._prep.append(prep)

    @property
    def passed(self):
        raise NotImplementedError

    @property
    def render(self):
        raise NotImplementedError


class TestSuiteBase(RunnableTest):
    """ Object representing a full runnable Test Suite on a single entity """
    def __init__(self):
        super(TestSuiteBase, self).__init__()
        self._tests = []
        self._prep = []

    def add_prep(self, prep):
        assert isinstance(prep, TestPrepBase)
        prep.parent = self
        self._prep.append(prep)

    def add_test(self, test):
        test.parent = self
        self._tests.append(test)

    def run_test(self):
        logger.debug("Running Test Suite : " + repr(self))
        for prep in self._prep:
            prep.run_prep()
        for test in self._tests:
            test.run_test()

    @property
    def passed(self):
        rval = True
        for test in self._tests:
            if test.passed is False:
                rval = False
        return rval

    def render(self):
        raise NotImplementedError

    def finish(self):
        for test in self._tests:
            test.finish()

    @property
    def tests(self):
        return self._tests
