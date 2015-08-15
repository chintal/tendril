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

from tendril.utils.config import INSTANCE_ROOT
default_target = os.path.join(INSTANCE_ROOT, 'scratch', 'testing')


@with_db
def render_test_report(serialno=None, outfolder=None, session=None):
    suites = analysis.get_test_suite_objects(serialno=serialno, session=session)
    for suite in suites:
        suite.finish()
