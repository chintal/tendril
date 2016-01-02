#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for views
"""

from flask import render_template
from flask_user import login_required

from . import testing as blueprint

from tendril.dox import testing as dxtesting
from tendril.utils.fsutils import Crumb

from tendril.testing import analysis
from tendril.entityhub import projects
from tendril.gedaif.conffile import ConfigsFile

from tendril.utils import vcs
from tendril.utils.db import with_db
from tendril.entityhub import serialnos
from tendril.entityhub.db import controller as sno_controller
from tendril.entityhub.db.model import SerialNumber


@with_db
def get_test_report(serialno=None, session=None):
    """
    Constructs and returns the stage components for the latest test results
    marked against the specified ``serialno``.

    Since this function is defined against the database, all arguments should
    be keyword arguments.

    :param serialno: The serial number of the device.
    :type serialno: :class:`str` or :class:`tendril.entityhub.db.SerialNumber`
    :param session: The database session. If None, the function will make
                    it's own.
    :return: The output file path.

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
          - A list of graphs, each graph being the htmlcontent generated
            by python-nvd3.
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

    .. todo:: Move this function into :mod:`tendril.testing.analysis` and
              have :func:`tendril.dox.testing.render_test_report` use the
              same infrastructure.

    """
    if serialno is None:
        raise ValueError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = sno_controller.get_serialno_object(sno=serialno,
                                                      session=session)

    devicetype = serialnos.get_serialno_efield(sno=serialno.sno,
                                               session=session)
    projectfolder = projects.cards[devicetype]
    gcf = ConfigsFile(projectfolder)

    suites = analysis.get_test_suite_objects(serialno=serialno.sno,
                                             session=session)
    instruments = {}
    for suite in suites:
        for test in suite._tests:
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
             'instruments': instruments
             }

    return stage


@blueprint.route('/result/<device_sno>')
@blueprint.route('/result/')
@login_required
def results(device_sno=None):
    # Presently only supports getting the latest result. A way to allow
    # any result to be retrieved would be nice.
    if device_sno is None:
        docs = dxtesting.get_all_test_reports()
        stage = {'docs': docs,
                 'crumbroot': '/testing',
                 'breadcrumbs': [Crumb(name="Testing", path=""),
                                 Crumb(name="Results", path="result/")],
                 }
        return render_template('test_results.html', stage=stage,
                               pagetitle="All Test Results")
    else:
        docs = dxtesting.get_latest_test_report(device_sno)
        stage = {'docs': docs,
                 'crumbroot': '/testing',
                 'breadcrumbs': [Crumb(name="Testing", path=""),
                                 Crumb(name="Reports", path="result/"),
                                 Crumb(name=device_sno, path="result/" + device_sno)],  # noqa
                 }
        stage.update(get_test_report(serialno=device_sno))
        return render_template('test_result_detail.html', stage=stage,
                               pagetitle=device_sno + " Test Result")


@blueprint.route('/')
@login_required
def main():
    latest = dxtesting.get_all_test_reports(limit=5)
    stage = {'latest': latest,
             'crumbroot': '/testing',
             'breadcrumbs': [Crumb(name="Testing", path="")],
             }
    return render_template('testing_main.html', stage=stage,
                           pagetitle='Testing')
