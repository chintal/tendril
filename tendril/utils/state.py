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
The Persistent State Utils Module (:mod:`tendril.utils.state`)
==============================================================

.. warning:: This module is deprecated in favor of
             :mod:`tendril.utils.db`, and it's dependencies have
             been purged from the tendril requirements.

This module uses :mod:`dataset` to provide a means to store persistent
state information.

The primary storage is an sqlite3 database, located within the INSTANCE_ROOT.
This storage is accessible by application code by importing this module's
:data:`state_ds` module variable, and the documentation of :mod:`dataset`
should be used interact directly with this object.

"""


import os
import dataset

from tendril.utils.config import INSTANCE_ROOT

import logging
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)
logging.getLogger('dataset.persistence.database').setLevel(logging.WARNING)


#: A :class:`dataset.Database` instance, attached to the sqlite3 database
#: located at ``db/state.db`` under the instance root, defined by
#: :data:``utils.config.INSTANCE_ROOT``
state_ds = dataset.connect(
    'sqlite:///' + os.path.join(INSTANCE_ROOT, 'db', 'state.db')
)
