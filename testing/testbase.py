"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


class TestPrepBase(object):
    """ Object representing a preparatory step for a Test """
    def __init__(self, parent):
        self._parent = parent
        self._apparatus = []


class TestMeasurementBase(object):
    """ Object representing a single measurement for a Test """
    def __init__(self, parent):
        self._parent = parent
        self._input = None
        self._output = None


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


class TestSuiteBase(RunnableTest):
    """ Object representing a full runnable Test Suite on a single entity """
    def __init__(self):
        super(TestSuiteBase, self).__init__()
        self._tests = []

    def add_test(self, test):
        assert isinstance(test, TestBase)
        self._tests.append(test)
