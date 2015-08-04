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


import time


class TestPrepBase(object):
    """ Object representing a preparatory step for a Test """
    def __init__(self, parent):
        self._parent = parent
        self._steps = []

    def run_prep(self):
        for step in self._steps:
            print step


class TestMeasurementBase(object):
    """ Object representing a single measurement for a Test """
    def __init__(self, parent):
        self._parent = parent

        # Any excitation, if necessary
        self._outputchannel = None
        self._output = None

        self._stime = None

        # Measurement
        self._inputchannel = None
        self._input = None
        self._inputtype = None

    def do_measurement(self):
        """
        This is an example measurement function. This should be overridden
        by the actual Test classes to perform the actual measurement, and
        this code can be used as a starting point.

        The result of the measurement would typically be some composition of
        instances of :class:`koala.utils.type.signalbase.SignalBase`.
        """
        if self._output is not None:
            if self._outputchannel is None:
                raise IOError("Output channel is not defined")
            self._outputchannel.set(self._output)

        if self._stime is not None:
            time.sleep(self._stime)

        if self._inputtype is not None:
            if self._inputchannel is None:
                raise IOError("Input channel is not defined")
            self._input = self._inputchannel.get()
            if not self._input.unitclass == self._inputtype:
                raise TypeError("Expected " + self._inputtype.unitclass + ", got " + type(self._input))

    def render(self):
        """
        This is an example render function. This should be overridden by the
        actual Test classes to render the actual result.

        Rendering means encoding the test result into a JSON representation,
        which can later be dumped into a postgres database.
        """
        raise NotImplementedError


class RunnableTest(object):
    def run_test(self):
        raise NotImplementedError

    def commit_results(self):
        raise NotImplementedError


class TestBase(RunnableTest):
    """ Object representing a full runnable Test of the same Measurement type"""
    def __init__(self, parent):
        self._parent = parent
        self._prep = []
        self._measurements = []
        self._result = None

    def run_test(self):
        for prep in self._prep:
            prep.run_prep()
        for measurement in self._measurements:
            measurement.do_measurement()

    def commit_results(self):
        pass


class TestSuiteBase(RunnableTest):
    """ Object representing a full runnable Test Suite on a single entity """
    def __init__(self):
        super(TestSuiteBase, self).__init__()
        self._tests = []

    def add_test(self, test):
        assert isinstance(test, TestBase)
        self._tests.append(test)

    def run_test(self):
        for test in self._tests:
            test.run_test()

    def commit_results(self):
        for test in self._tests:
            test.commit_results()
