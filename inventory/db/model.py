"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy import Column, String

from utils.db import DeclBase
from utils.db import BaseMixin
from utils.db import TimestampMixin


class InventoryLocationCode(BaseMixin, DeclBase):
    name = Column(String)

    def __repr__(self):
        return "<InventoryLocationCode(id = %s, name='%s')>" % (self.id, self.name)


