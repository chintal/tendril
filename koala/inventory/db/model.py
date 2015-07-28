"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy import Column, String

from koala.utils.db import DeclBase
from koala.utils.db import BaseMixin


class InventoryLocationCode(BaseMixin, DeclBase):
    name = Column(String)

    def __repr__(self):
        return "<InventoryLocationCode(id = %s, name='%s')>" % (self.id, self.name)
