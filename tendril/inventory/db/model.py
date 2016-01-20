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

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class InventoryLocationCode(BaseMixin, DeclBase):
    name = Column(String)

    def __repr__(self):
        return "<InventoryLocationCode" \
               "(id = %s, name='%s')>" % (self.id, self.name)


class InventoryIndent(DeclBase, BaseMixin, TimestampMixin):

    title = Column(String(60), unique=False, nullable=True)
    desc = Column(String, unique=False, nullable=True)

    type = Column(
            Enum('production', 'prototype', 'testing', 'support', 'rd',
                 name='indent_type'),
            nullable=False, default='active', server_default='production'
    )

    status = Column(
            Enum('active', 'pending', 'archived', 'reversed',
                 name='indent_status'),
            nullable=False, default='active', server_default='active'
    )

    # Relationships
    # # Documents
    # doc_id = Column(Integer, ForeignKey('DocStoreDocument.id'),
    #                 nullable=True, unique=True)
    # doc = relationship("DocStoreDocument", uselist=False)
    #
    # doc_cobom_id = Column(Integer, ForeignKey('DocStoreDocument.id'),
    #                       nullable=True, unique=True)
    # doc_cobom = relationship("DocStoreDocument", uselist=False)

    # Serial Numbers
    requested_by_id = Column(Integer, ForeignKey('User.id'),
                             nullable=False, unique=False)
    requested_by = relationship("User", backref='indents')

    serialno_id = Column(Integer, ForeignKey('SerialNumber.id'),
                         nullable=False)
    serialno = relationship(
            "SerialNumber", uselist=False, cascade="all",
            primaryjoin="InventoryIndent.serialno_id == SerialNumber.id"
    )

    auth_parent_id = Column(Integer, ForeignKey('SerialNumber.id'),
                            nullable=True)
    auth_parent = relationship(
            "SerialNumber", backref='direct_indents', uselist=False,
            primaryjoin="InventoryIndent.auth_parent_id == SerialNumber.id"
    )

    # Raw Data
    cobom_id = None
    cobom = None

    def __repr__(self):
        return "<InventoryIndent DB ({0})>".format(self.sno)

