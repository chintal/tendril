"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import os
import re
import numpy

from tendril.utils.db import with_db
from tendril.entityhub import serialnos
from tendril.entityhub import projects
from tendril.entityhub.db import controller as sno_controller
from tendril.boms.electronics import import_pcb
from tendril.dox.render import make_histogram
from tendril.utils.fsutils import TEMPDIR
from tendril.utils.fsutils import get_tempname

from db import controller
from testbase import TestSuiteBase
from tests import get_test_object
from testrunner import get_electronics_test_suites

from matplotlib import pyplot

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

rex_class = re.compile(ur'^<class \'(?P<cl>[a-zA-Z0-9.]+)\'>$')


def sort_by_order(desc, order):
    rval = []
    for d in order:
        for od, on in desc:
            if d == od:
                rval.append((od, on))
                desc.remove((od, on))
                break
    rval.extend(desc)
    return rval


@with_db
def get_test_suite_objects(serialno=None, order_by='FILE_ORDER',
                           session=None):
    # This reconstructs the test objects from the database. Using SQLAlchemy
    # as the ORM that it is, and letting it handle the object creation would
    # be infinitely better. It isn't done here since the models are separate
    # from the actual test objects, which in turn have other dependencies.
    # Integrating the models with the classes should be considered in the
    # future when there is time.
    # suite_names = controller.get_test_suite_names(serialno=serialno,
    #                                               session=session)
    suite_descs = controller.get_test_suite_descs(serialno=serialno,
                                                  session=session)
    devicetype = serialnos.get_serialno_efield(sno=serialno, session=session)
    projectfolder = projects.cards[devicetype]
    bomobj = import_pcb(cardfolder=projectfolder)
    # Perhaps this bomobject should not be recreated on the fly.
    bomobj.configure_motifs(devicetype)

    if order_by == 'FILE_ORDER':

        logger.info("Creating dummy test suites for file ordering")
        dummy_suites = get_electronics_test_suites(None, devicetype,
                                                   projectfolder,
                                                   offline=True)
        ldummy_suites = []
        for suite in dummy_suites:
            suite.dummy = True
            ldummy_suites.append(suite)

        file_order = [(x.desc, [(y.desc, y.passfailonly) for y in x.tests])
                      for x in ldummy_suites]
        suite_order = [x[0] for x in file_order]
        test_order = {x[0]: x[1] for x in file_order}

    elif order_by == 'DONT_CARE':
        suite_order = []
        test_order = {}

    else:
        raise ValueError('Unknown order_by heuristic : ' + order_by)

    suites = []
    suite_descs = sort_by_order(suite_descs, suite_order)

    # for suite_name in suite_names:
    for desc, name in suite_descs:
        suite_db_obj = controller.get_latest_test_suite(
            serialno=serialno, suite_class=name, descr=desc, session=session
        )
        if suite_db_obj.suite_class == \
                "<class 'tendril.testing.testbase.TestSuiteBase'>":
            suite_obj = TestSuiteBase()
        else:
            raise ValueError("Unrecognized suite_class : " +
                             suite_db_obj.suite_class)

        suite_obj.desc = suite_db_obj.desc
        suite_obj.title = suite_db_obj.title
        suite_obj.ts = suite_db_obj.created_at
        suite_obj.serialno = serialno
        if order_by == 'FILE_ORDER':
            test_display_params = {x[0]: x[1]
                                   for x in test_order[suite_obj.desc]}

        for test_db_obj in suite_db_obj.tests:
            class_name = rex_class.match(test_db_obj.test_class).group('cl')

            test_obj = get_test_object(class_name, offline=True)
            test_obj.desc = test_db_obj.desc
            test_obj.title = test_db_obj.title
            test_obj.ts = test_db_obj.created_at
            test_obj.use_bom(bomobj)
            test_obj.load_result_from_obj(test_db_obj.result)
            if order_by == 'FILE_ORDER':
                test_obj.passfailonly = test_display_params[test_obj.desc]
            suite_obj.add_test(test_obj)
            # Crosscheck test passed?

        # Crosscheck suite passed?

        suites.append(suite_obj)

    return suites


class ResultGraphCollector(object):
    def __init__(self, dummy_graph, parent):
        self._parent = parent
        a, b, self._dummy_graph_params, self._dummy_graph_title = dummy_graph
        self._collected = []

    def add_graph(self, graph):
        self._collected.append(graph)

    def _make_graph(self, color='black', lw=2, marker=None,
                    xscale='linear', yscale='linear',
                    xlabel='', ylabel=''):
        outpath = os.path.join(TEMPDIR,
                               'GRAPH_GROUP_' + get_tempname() + '.png'
                               )
        for graph in self._collected:
            pyplot.plot(graph[0], graph[1], color=color, lw=lw, marker=marker)
        pyplot.xscale(xscale)
        pyplot.yscale(yscale)
        pyplot.grid(True, which='major', color='0.3', linestyle='-')
        pyplot.grid(True, which='minor', color='0.3')
        pyplot.xlabel(xlabel, fontsize=20)
        pyplot.ylabel(ylabel, fontsize=20)
        pyplot.tick_params(axis='both', which='major', labelsize=16)
        pyplot.tick_params(axis='both', which='minor', labelsize=8)
        pyplot.tight_layout()
        pyplot.savefig(outpath)
        pyplot.close()
        return outpath

    def _make_graphs(self):
        outpath = self._make_graph(**self._dummy_graph_params)
        return outpath, self._dummy_graph_title

    @property
    def graphs(self):
        return [self._make_graphs()]


class ResultLineCollector(object):
    def __init__(self, dummy_line, parent):
        self._parent = parent
        self._dummy_line = dummy_line
        self._parser = dummy_line.measured
        self._collected = []

    def add_line(self, line):
        if self._parser is not None:
            self._collected.append(self._parser(line.measured))
        else:
            self._collected.append(line.measured)

    def get_range(self):
        if self._dummy_line.expected is None:
            return None
        center, op, merror = self._dummy_line.expected.split(' ')
        center = self._parser(center)
        merror = self._parser(merror)
        return float(center - merror), float(center + merror)

    @property
    def graphs(self):
        if self._parser is not None:
            # rng = self.get_range()
            rng = None
            path = os.path.join(TEMPDIR, 'hist_' + get_tempname() + '.png')
            hist = make_histogram(path, [float(x) for x in self._collected],
                                  xlabel=self.desc, x_range=rng)
            return [(hist, self._parent.desc)]
        return []

    @property
    def desc(self):
        return self._dummy_line.desc

    @property
    def expected(self):
        return self._dummy_line.expected

    @property
    def measured(self):
        if self._parser is not None:
            return (
                sum(self._collected) / len(self._collected)
            ).quantized_repr
        else:
            return 'VARIOUS'

    @property
    def maxp(self):
        if self._parser is not None:
            return max(self._collected).quantized_repr
        return None

    @property
    def minp(self):
        if self._parser is not None:
            return min(self._collected).quantized_repr
        return None

    @property
    def spread(self):
        if self._parser is not None:
            spread = self.maxp - self.minp
            return spread.integral_repr
        else:
            return None

    @property
    def std_dev(self):
        if self._parser is not None:
            return self._parser(
                numpy.std([float(x) for x in self._collected])
            ).integral_repr
        return None


class ResultTestCollector(object):
    def __init__(self, dummy_test, include_failed=False):
        self._line_collectors = []
        self._graph_collectors = []
        self._dummy_test = dummy_test
        self._total_count = 0
        self._passed_count = 0
        self._include_failed = include_failed
        for line in dummy_test.lines:
            self._line_collectors.append(ResultLineCollector(line, self))
        for graph in dummy_test.graphs_data:
            self._graph_collectors.append(ResultGraphCollector(graph, self))

    @property
    def classname(self):
        return str(self._dummy_test.__class__)

    @property
    def desc(self):
        return self._dummy_test.desc

    @property
    def title(self):
        return self._dummy_test.title

    def add_test(self, test):
        if str(test.__class__) != str(self._dummy_test.__class__):
            raise TypeError(
                "Test Class does not match : " + str(test.__class__) +
                ", expected " + str(self._dummy_test.__class__)
            )
        self._total_count += 1
        if test.passed is True:
            self._passed_count += 1
        if self._include_failed is True or test.passed is True:
            for idx, line in enumerate(test.lines):
                self._line_collectors[idx].add_line(line)
            for idx, graph in enumerate(test.graphs_data):
                self._graph_collectors[idx].add_graph(graph)

    @property
    def graphs(self):
        rval = []
        for collectors in self._graph_collectors:
            rval.extend(collectors.graphs)
        for collectors in self._line_collectors:
            rval.extend(collectors.graphs)
        return rval

    @property
    def lines(self):
        return self._line_collectors

    @property
    def total_count(self):
        return self._total_count

    @property
    def passed_count(self):
        return self._passed_count


class ResultSuiteCollector(object):
    def __init__(self, dummy_suite, include_failed=False):
        self._test_collectors = []
        self._dummy_suite = dummy_suite
        self._total_count = 0
        self._passed_count = 0
        for test in dummy_suite.tests:
            self._test_collectors.append(
                ResultTestCollector(test, include_failed=include_failed)
            )

    def get_collector(self, name, desc):
        rval = []
        for collector in self._test_collectors:
            if collector.classname == name:
                rval.append(collector)
        if len(rval) == 1:
            return rval[0]
        else:
            for collector in rval:
                if collector.desc == desc:
                    return collector
            raise ValueError("Can't find collector : " + name + " " + desc)

    def add_suite(self, suite):
        if str(suite.__class__) != str(self._dummy_suite.__class__):
            raise TypeError(
                "Suite Class does not match : " + str(suite.__class__) +
                ", expected " + str(self._dummy_suite.__class__)
            )
        self._total_count += 1
        if suite.passed is True:
            self._passed_count += 1
        for idx, test in enumerate(suite.tests):
            collector = self.get_collector(str(test.__class__), test.desc)
            collector.add_test(test)

    @property
    def graphs(self):
        rval = []
        for collectors in self._test_collectors:
            rval.extend(collectors.graphs)
        return rval

    @property
    def classname(self):
        return str(self._dummy_suite.__class__)

    @property
    def desc(self):
        return self._dummy_suite.desc

    @property
    def title(self):
        return self._dummy_suite.title

    @property
    def tests(self):
        return self._test_collectors

    @property
    def total_count(self):
        return self._total_count

    @property
    def passed_count(self):
        return self._passed_count


class ResultCollector(object):
    def __init__(self, dummy_suites, include_failed=False):
        self._suite_collectors = []
        for suite in dummy_suites:
            self._suite_collectors.append(
                ResultSuiteCollector(suite, include_failed=include_failed)
            )

    def add_suites_set(self, suites):
        for idx, suite in enumerate(suites):
            self._suite_collectors[idx].add_suite(suite)

    @property
    def graphs(self):
        rval = []
        for collectors in self._suite_collectors:
            rval.extend(collectors.graphs)
        return rval

    @property
    def suites(self):
        return self._suite_collectors


@with_db
def get_device_test_summary(devicetype=None, include_failed=False,
                            session=None):
    projectfolder = projects.cards[devicetype]
    bomobj = import_pcb(cardfolder=projectfolder)
    bomobj.configure_motifs(devicetype)

    logger.info("Creating dummy test suites")
    dummy_suites = get_electronics_test_suites(None, devicetype,
                                               projectfolder,
                                               offline=True)
    for suite in dummy_suites:
        suite.dummy = True

    collector = ResultCollector(dummy_suites, include_failed=include_failed)

    snos = sno_controller.get_serialnos_by_efield(efield=devicetype,
                                                  session=session)

    for sno in snos:
        suites = get_test_suite_objects(serialno=sno.sno, session=session)
        if len(suites) > 0:
            collector.add_suites_set(suites)

    return collector
