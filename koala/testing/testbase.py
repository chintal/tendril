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

    def do_measurement(self):
        if self._output is not None:
            if self._outputchannel is None:
                raise IOError("Output channel is not defined")
            self._outputchannel.set(self._output)

        if self._stime is not None:
            time.sleep(self._stime)

        if self._input is not None:
            if self._inputchannel is None:
                raise IOError("Input channel is not defined")
            self._input = self._inputchannel.get()


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
        self._runner = None

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

