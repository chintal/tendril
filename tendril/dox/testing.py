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
Testing Dox Module (:mod:`tendril.dox.testing`)
===============================================

This module provides functions to generate testing documents.

The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

.. seealso:: :mod:`tendril.testing.analysis`, which does much of
             the heavy lifting

.. rubric:: Document Generators

.. autosummary::

    render_test_report
    render_device_summary

"""

import os

from tendril.testing import analysis
from tendril.utils.db import with_db
from tendril.entityhub import serialnos
from tendril.entityhub import projects
from tendril.gedaif.conffile import ConfigsFile
from tendril.utils import vcs
from tendril.entityhub.db.model import SerialNumber
from tendril.entityhub.db import controller as sno_controller

from render import render_pdf
import docstore

from tendril.utils.config import INSTANCE_ROOT
from tendril.utils import log

logger = log.get_logger(__name__, log.DEFAULT)
default_target = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')


@with_db
def render_test_report(serialno=None, outfolder=None, session=None):
    """
    Renders the latest test results marked against the specified ``serialno``.

    Since this function is defined against the database, all arguments should
    be keyword arguments.

    :param serialno: The serial number of the device.
    :type serialno: :class:`str` or :class:`tendril.entityhub.db.SerialNumber`
    :param outfolder: The folder in which the output file should be created.
    :type outfolder: str
    :param session: The database session. If None, the function will make
                    it's own.
    :return: The output file path.

    .. rubric:: Template Used

    ``tendril/dox/templates/testing/test_report_template.tex``
    (:download:`Included version
    <../../tendril/dox/templates/testing/test_report_template.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``sno``
          - Serial number of the device.
        * - ``testdate``
          - The timestamp of the latest test suite.
        * - ``devicetype``
          - The device type.
        * - ``desc``
          - The device description.
        * - ``svnrevision``
          - The VCS revision of the project config file.
        * - ``svnrepo``
          - The VCS repository containing the project
        * - ``graphs``
          - A list of graphs, each graph being a list of tuples of
            (graphpath, graphtitle)
        * - ``instruments``
          - A list of instrument ident strings, one for each unique
            instrument used in the suites.
        * - ``suites``
          - A list of instances of
            :class:`tendril.testing.testbase.TestSuiteBase` or its subclasses.

    Note that the ``suites`` provided to the template are typically
    expected to be offline test suites which are reconstructed from the
    database.

    .. seealso:: :func:`tendril.testing.analysis.get_test_suite_objects`

    """
    if serialno is None:
        raise ValueError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = sno_controller.get_serialno_object(sno=serialno,
                                                      session=session)
    if outfolder is None:
        outfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')

    template = os.path.join('testing', 'test_report_template.tex')
    outpath = os.path.join(outfolder,
                           'TEST-REPORT-' + serialno.sno + '.pdf')

    devicetype = serialnos.get_serialno_efield(sno=serialno.sno,
                                               session=session)
    projectfolder = projects.cards[devicetype]
    gcf = ConfigsFile(projectfolder)

    suites = analysis.get_test_suite_objects(serialno=serialno.sno,
                                             session=session)
    graphs = []
    instruments = {}
    for suite in suites:
        for test in suite._tests:
            graphs.extend(test.graphs)
            graphs.extend(test.histograms)
            if test._inststr is not None and \
                    test._inststr not in instruments.keys():
                instruments[test._inststr] = len(instruments.keys()) + 1

    stage = {'suites': [x.render_dox() for x in suites],
             'sno': serialno.sno,
             'testdate': max([x.ts for x in suites]).format(),
             'devicetype': devicetype,
             'desc': gcf.description(devicetype),
             'svnrevision': vcs.get_path_revision(projectfolder),
             'svnrepo': vcs.get_path_repository(projectfolder),
             'graphs': graphs,
             'instruments': instruments
             }

    return render_pdf(stage, template, outpath)


def render_device_summary(devicetype, include_failed=False, outfolder=None):
    """
    Renders a summary of all of the latest test results marked against the
    serial numbers of the specified ``devicetype``.

    :param devicetype: The type of device for which a summary is desired.
    :type devicetype: str
    :param outfolder: The folder in which the output file should be created.
    :type outfolder: str
    :param include_failed: Whether failed test results should be included in
                      the graphs and the statistical analysis. Default False.
    :type include_failed: bool
    :return: The output file path.

    .. rubric:: Template Used

    ``tendril/dox/templates/testing/test_device_summary_template.tex``
    (:download:`Included version
    <../../tendril/dox/templates/testing/test_device_summary_template.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``devicetype``
          - The device type.
        * - ``desc``
          - The device description.
        * - ``svnrevision``
          - The VCS revision of the project config file.
        * - ``svnrepo``
          - The VCS repository containing the project
        * - ``graphs``
          - A list of graphs, each graph being a list of tuples of
            (graphpath, graphtitle)
        * - ``collector``
          - An instance of :class:`tendril.testing.analysis.ResultCollector`,
            containing the collated test results.

    .. seealso:: :func:`tendril.testing.analysis.get_device_test_summary`

    """
    if outfolder is None:
        outfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')
    template = os.path.join('testing', 'test_device_summary_template.tex')
    outpath = os.path.join(outfolder,
                           'TEST-DEVICE-SUMMARY-' + devicetype + '.pdf')

    projectfolder = projects.cards[devicetype]
    gcf = ConfigsFile(projectfolder)

    summary = analysis.get_device_test_summary(devicetype=devicetype,
                                               include_failed=include_failed)
    graphs = summary.graphs

    stage = {'devicetype': devicetype,
             'desc': gcf.description(devicetype),
             'svnrevision': vcs.get_path_revision(projectfolder),
             'svnrepo': vcs.get_path_repository(projectfolder),
             'graphs': graphs,
             'collector': summary
             }

    return render_pdf(stage, template, outpath)


def get_all_test_reports(limit=None):
    return docstore.get_docs_list_for_sno_doctype(serialno=None,
                                                  doctype='TEST-RESULT',
                                                  limit=limit)


def get_latest_test_report(serialno=None):
    return docstore.get_docs_list_for_sno_doctype(serialno=serialno,
                                                  doctype='TEST-RESULT',
                                                  limit=1)
