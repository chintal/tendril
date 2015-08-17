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
logger = log.get_logger(__name__, log.DEFAULT)

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

from tendril.utils.config import INSTANCE_ROOT
default_target = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')


@with_db
def render_test_report(serialno=None, outfolder=None, session=None):
    if serialno is None:
        raise ValueError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = sno_controller.get_serialno_object(sno=serialno, session=session)
    if outfolder is None:
        outfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')

    template = os.path.join('testing', 'test_report_template.tex')
    outpath = os.path.join(outfolder, 'TEST-REPORT-' + serialno.sno + '.pdf')

    devicetype = serialnos.get_serialno_efield(sno=serialno.sno, session=session)
    projectfolder = projects.cards[devicetype]
    gcf = ConfigsFile(projectfolder)

    suites = analysis.get_test_suite_objects(serialno=serialno.sno, session=session)
    graphs = []
    instruments = {}
    for suite in suites:
        for test in suite._tests:
            graphs.extend(test.graphs)
            if test._inststr is not None and test._inststr not in instruments.keys():
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


def render_device_summary(devicetype, outfolder=None):
    if outfolder is None:
        outfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')
    template = os.path.join('testing', 'test_device_summary_template.tex')
    outpath = os.path.join(outfolder, 'TEST-DEVICE-SUMMARY-' + devicetype + '.pdf')

    projectfolder = projects.cards[devicetype]
    gcf = ConfigsFile(projectfolder)

    summary = analysis.get_device_test_summary(devicetype=devicetype)
    graphs = summary.graphs

    stage = {
             'devicetype': devicetype,
             'desc': gcf.description(devicetype),
             'svnrevision': vcs.get_path_revision(projectfolder),
             'svnrepo': vcs.get_path_repository(projectfolder),
             'graphs': graphs,
             'collector': summary
             }

    return render_pdf(stage, template, outpath, remove_sources=False)
