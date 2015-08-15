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

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

# TODO  Replace with colorama or so for both
from tendril.utils.progressbar import terminal
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
        print terminal.YELLOW + self._string + terminal.NORMAL
        raw_input(terminal.YELLOW + "Press Enter to continue..." + terminal.NORMAL)


class RunnableTest(object):
    def __init__(self):
        self._serialno = None
        self._parent = None
        self._desc = None
        self._title = None
        self._ts = None

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
        logger.info(repr(self) + " :: Result : " + str(self.passed))

    @property
    def desc(self):
        return self._desc

    @desc.setter
    def desc(self, value):
        self._desc = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def ts(self):
        return self._ts

    @ts.setter
    def ts(self, value):
        if isinstance(value, arrow.Arrow):
            self._ts = value
        else:
            self._ts = arrow.get(value)


class TestBase(RunnableTest):
    """ Object representing a full runnable Test of the same Measurement type"""
    def __init__(self, offline=False):
        super(TestBase, self).__init__()
        self._prep = []
        self._measurements = []
        self._result = None
        self.variables = {}
        self._bom_object = None
        self._offline = offline

    def add_measurement(self, measurement):
        measurement.parent = self
        self._measurements.append(measurement)
        return measurement

    def run_test(self):
        logger.debug("Running Test : " + repr(self))
        if self._offline is True:
            raise IOError("Cannot run an offline test")
        for prep in self._prep:
            prep.run_prep()
        for measurement in self._measurements:
            measurement.do_measurement()

    def _load_variable(self, name, typeclass):
        try:
            rv = typeclass(self.variables[name])
            return rv
        except ValueError:
            value = self.variables[name]
            if ':' in value:
                motif_refdes, elem = value.split(':')
                motif = self._bom_object.get_motif_by_refdes(motif_refdes)
                value = getattr(motif, elem)
            value = typeclass(value)
        return value

    def configure(self, **kwargs):
        self.variables.update(kwargs)

    def use_bom(self, bomobj):
        self._bom_object = bomobj

    def add_prep(self, prep):
        prep.parent = self
        self._prep.append(prep)

    @property
    def passed(self):
        raise NotImplementedError

    @property
    def render(self):
        raise NotImplementedError

    @staticmethod
    def _pr_repr(string):
        if string[0] == string[-1] == "'":
            return string[1:-1]
        else:
            return string

    def load_result_from_obj(self, result_db_obj):
        raise NotImplementedError

    def finish(self):
        if self.passed is True:
            result = terminal.GREEN + '[PASSED]' + terminal.NORMAL
        else:
            result = terminal.RED + '[FAILED]' + terminal.NORMAL
        hline = '-' * 80
        print terminal.YELLOW + hline + terminal.NORMAL
        print "{0:<70} {1:<10}".format(terminal.YELLOW + self.desc + terminal.NORMAL, result)
        print "{0}".format(self.title)
        print "{0}".format(repr(self))


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
        hline = '-' * 80
        print terminal.YELLOW + hline + terminal.NORMAL
        if self.passed is True:
            result = terminal.GREEN + '[PASSED]' + terminal.NORMAL
        else:
            result = terminal.RED + '[FAILED]' + terminal.NORMAL
        print "{0:<70} {1:<10}".format(self.desc, result)
        print "{0}".format(repr(self))
        print terminal.YELLOW + hline + terminal.NORMAL

    @property
    def tests(self):
        return self._tests
