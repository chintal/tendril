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

from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import synonym

from sqlalchemy import UniqueConstraint
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship

from tendril.utils.db import DeclBase
from tendril.utils.db import BaseMixin
from tendril.utils.db import TimestampMixin

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class SourcingVendor(BaseMixin, DeclBase):
    name = Column(String, nullable=False, unique=True)
    dname = Column(String, nullable=True, unique=False)
    type = Column(String, nullable=False, unique=False)
    mapfile_base = Column(String, nullable=False, unique=True)
    pclass_str = Column(String, nullable=False, unique=False)
    status = Column(
            Enum('active', 'suspended', 'defunct', name='vendor_status'),
            nullable=False,
            default='active',
            server_default='active'
    )

    # Derived Fields
    @property
    def pclass(self):
        return self.pclass_str.split(':')

    @pclass.setter
    def pclass(self, value):
        self.pclass_str = ":".join([x.strip() for x in value])

    pclass = synonym('pclass_str', descriptor=pclass)

    # Relationships
    maps = relationship("VendorPartMap")

    # Housekeeping
    def __repr__(self):
        return "<SourcingVendor " \
               "(id = %s, name='%s')>" % (self.id, self.name)


class VendorPartMap(DeclBase, BaseMixin, TimestampMixin):
    ident = Column(String, unique=False, nullable=False)
    strategy = Column(String, unique=False, nullable=True)

    # Derived Fields
    @property
    def umap(self):
        return [x for x in self.vpnos if x.type == 'manual']

    @property
    def amap(self):
        return [x for x in self.vpnos if x.type == 'auto']

    @property
    def map(self):
        return self.vpnos

    # Relationships
    vendor_id = Column(Integer, ForeignKey('SourcingVendor.id'))
    vpnos = relationship("VendorPartNumber")

    # Constraints
    __table_args__ = (
        UniqueConstraint('vendor_id', 'ident', name="constraint_vmap_ident"),
    )


class VendorPartNumber(DeclBase, BaseMixin, TimestampMixin):
    vpno = Column(String, unique=False, nullable=False)
    type = Column(
            Enum('auto', 'manual', name='map_type'),
            nullable=False,
            default='auto',
            server_default='auto'
    )

    # Relationships
    vpmap_id = Column(Integer, ForeignKey('VendorPartMap.id'))

    # Constraints
    __table_args__ = (
        UniqueConstraint('vpmap_id', 'vpno', name="constraint_vmap_vpno"),
    )
