"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.DEFAULT)

import electronics


class CompositeOrderElem(object):
    pass


class CompositeOrder(object):
    def __init__(self):
        self._allowed_electonics_vendors = []
        for vendor in electronics.vendor_list:
            self._allowed_electonics_vendors.append(vendor)


