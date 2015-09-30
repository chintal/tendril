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

import os
import arrow
from collections import namedtuple

from tendril.utils.fsutils import TEMPDIR
from tendril.utils.fsutils import get_tempname

from colorama import Fore
from tendril.utils import terminal
from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


TestLine = namedtuple('TestLine', ['desc', 'expected', 'measured'])


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
        print Fore.YELLOW + self._string + Fore.RESET
        raw_input(Fore.YELLOW +
                  "Press Enter to continue..." +
                  Fore.RESET)


class RunnableTest(object):
    def __init__(self):
        self._serialno = None
        self._parent = None
        self._desc = None
        self._title = None
        self._ts = None
        self._dummy = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        self._parent = value

    @property
    def dummy(self):
        if self._dummy is not None:
            return self._dummy
        else:
            if self._parent is not None:
                return self._parent.dummy
            else:
                return False

    @dummy.setter
    def dummy(self, value):
        self._dummy = value

    @property
    def serialno(self):
        # override_sno = "QTJDT7SL"
        # return override_sno
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

    def destroy(self):
        raise NotImplementedError

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

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__, self.desc)


class TestBase(RunnableTest):
    """
    Object representing a full runnable Test of the same Measurement type
    """
    def __init__(self, offline=False):
        super(TestBase, self).__init__()
        self._prep = []
        self._measurements = []
        self._result = None
        self.variables = {}
        self._bom_object = None
        self._offline = offline
        self._inststr = None
        self._passfailonly = False

    @property
    def offline(self):
        return self._offline

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
        self.ts = arrow.utcnow()

    def _load_variable(self, name, typeclass):
        try:
            rv = typeclass(self.variables[name])
            return rv
        except ValueError:
            value = self.variables[name]
            if ':' in value:
                motif_refdes, elem = value.split(':')
                motif = self._bom_object.get_motif_by_refdes(motif_refdes)
                try:
                    value = getattr(motif, elem)
                except (TypeError, AttributeError):
                    logger.error("Error getting element " + repr(elem) +
                                 " from Motif " + repr(motif) +
                                 ", required by " + value)
                    logger.error("Bomobject configured for " +
                                 self._bom_object.configured_for)
                    raise
            value = typeclass(value)
        except KeyError:
            raise
        return value

    def configure(self, **kwargs):
        self.variables.update(kwargs)
        if 'passfailonly' in kwargs.keys():
            self._passfailonly = kwargs['passfailonly']

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

    def render_dox(self):
        test_dict = {'desc': self.desc,
                     'title': self.title,
                     'ts': self.ts.format(),
                     'passed':
                     ('PASSED' if self.passed is True else 'FAILED'),
                     'measurements':
                     [x.render_dox() for x in self._measurements],
                     'instrument': self._inststr,
                     'lines': self.lines,
                     'passfailonly': self.passfailonly,
                     }
        return test_dict

    @property
    def passfailonly(self):
        try:
            return self._passfailonly
        except AttributeError:
            return False

    @passfailonly.setter
    def passfailonly(self, value):
        self._passfailonly = value

    @property
    def lines(self):
        return []

    @property
    def graphs(self):
        return self._make_graphs()

    @property
    def histograms(self):
        return self._make_histograms()

    @staticmethod
    def get_new_graph_path():
        return os.path.join(TEMPDIR, 'graph' + get_tempname() + '.png')

    @staticmethod
    def _make_graph(*args, **kwargs):
        from tendril.dox.render import make_graph
        return make_graph(*args, **kwargs)

    @staticmethod
    def _make_histogram(*args, **kwargs):
        from tendril.dox.render import make_histogram
        return make_histogram(*args, **kwargs)

    def _get_graphs_data(self):
        return []

    def _get_histograms_data(self):
        return []

    @property
    def graphs_data(self):
        return self._get_graphs_data()

    @property
    def histograms_data(self):
        return self._get_histograms_data()

    def _make_graphs(self):
        rval = []
        for plotdata_x, plotdata_y, params, title in self._get_graphs_data():
            plt_path = self.get_new_graph_path()
            self._make_graph(plt_path, plotdata_y, plotdata_x, **params)
            rval.append((plt_path, self.desc + ' ' + title))
        return rval

    def _make_histograms(self):
        rval = []
        for plotdata_y, params, title in self._get_histograms_data():
            plt_path = self.get_new_graph_path()
            self._make_histogram(plt_path, plotdata_y, **params)
            rval.append((plt_path, self.desc + ' ' + title))
        return rval

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
            result = Fore.GREEN + '[PASSED]' + Fore.RESET
        else:
            result = Fore.RED + '[FAILED]' + Fore.RESET
        width = terminal.get_terminal_width()
        hline = '-' * 80
        print Fore.YELLOW + hline + Fore.RESET
        fstring = "{0}{1:<" + str(width-10) + "}{2} {3:>9}"
        print fstring.format(
            Fore.YELLOW, (self.desc or 'None'), Fore.NORMAL, result
        )
        print "{0}".format(self.title)
        print "{0}".format(repr(self))

    def destroy(self):
        pass


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

    def render_dox(self):
        suite_dict = {
            'desc': self.desc,
            'title': self.title,
            'ts': self.ts.format(),
            'passed': ('PASSED' if self.passed is True else 'FAILED'),
            'tests': [x.render_dox() for x in self._tests]
        }
        return suite_dict

    def finish(self):
        for test in self._tests:
            test.finish()
        width = terminal.get_terminal_width()
        hline = '-' * width
        hcolor = Fore.CYAN
        print hcolor + hline + Fore.RESET
        if self.passed is True:
            result = Fore.GREEN + '[PASSED]' + Fore.RESET
        else:
            result = Fore.RED + '[FAILED]' + Fore.RESET
        fstring = "{0}{1:<" + str(width-10) + "}{2} {3:>9}"
        print fstring.format(
            hcolor, (self.desc or 'None'), Fore.NORMAL,  result
        )
        print "{0}{1}{2}".format(hcolor, repr(self), Fore.RESET)
        print hcolor + hline + Fore.RESET

    def destroy(self):
        for test in self._tests:
            test.destroy()

    @property
    def tests(self):
        return self._tests

    @property
    def test_descs(self):
        return [x.desc for x in self._tests]

    def get_test_by_desc(self, desc):
        for test in self._tests:
            if test.desc == desc:
                return test
