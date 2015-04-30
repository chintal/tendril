"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import os

from entityhub.guidelines import QtyGuidelines
from utils.config import INSTANCE_ROOT


electronics_qty_file = os.path.join(INSTANCE_ROOT, 'inventory', 'guidelines', 'electronics-qty.yaml')
logger.info("Loading Electronics Inventory Qty Guidelines from file : " + os.linesep + electronics_qty_file)
electronics_qty = QtyGuidelines(electronics_qty_file)

