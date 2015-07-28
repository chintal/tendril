"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import os
import dataset

import logging
logging.getLogger('dataset.persistence.database').setLevel(logging.WARNING)

from koala.utils.config import INSTANCE_ROOT

state_ds = dataset.connect('sqlite:///' + os.path.join(INSTANCE_ROOT, 'db', 'state.db'))
