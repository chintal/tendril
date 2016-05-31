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
from sqlalchemy import Index
from sqlalchemy.orm import synonym

from sqlalchemy import UniqueConstraint
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref

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

    # Housekeeping
    def __repr__(self):
        return "<SourcingVendor " \
               "(id = %s, name='%s')>" % (self.id, self.name)


class SourcingVendorDetail(DeclBase, BaseMixin):
    dname = Column(String, unique=False, nullable=False)
    currency_code = Column(String, unique=False, nullable=False)
    currency_symbol = Column(String, unique=False, nullable=False)

    # Relationships
    vendor_id = Column(Integer, ForeignKey('SourcingVendor.id'),
                       unique=True, nullable=False)
    vendor = relationship(
        "SourcingVendor",
        backref=backref('detail', cascade='all, delete-orphan'),
        lazy='joined'
    )


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
    vendor_id = Column(Integer, ForeignKey('SourcingVendor.id'),
                       unique=False, nullable=False)
    vendor = relationship(
        "SourcingVendor",
        backref=backref('maps', cascade='all, delete-orphan')
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('vendor_id', 'ident', name="constraint_vmap_ident"),
        Index('ix_vid_ident', 'vendor_id', 'ident')
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
    vpmap_id = Column(Integer, ForeignKey('VendorPartMap.id'),
                      unique=False, nullable=False, index=True)
    vpmap = relationship(
        "VendorPartMap",
        backref=backref('vpnos', cascade='all, delete-orphan'),
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('vpmap_id', 'vpno', name="constraint_vmap_vpno"),
        Index('ix_vpmap_vpno', 'vpmap_id', 'vpno')
    )
    # TODO Add vpno <-> vendor constraint?


class VendorPartDetail(DeclBase, BaseMixin, TimestampMixin):
    vqtyavail = Column(Integer, unique=False, nullable=True)
    manufacturer = Column(String, unique=False, nullable=True)
    mpartno = Column(String, unique=False, nullable=True)
    vpartdesc = Column(String, unique=False, nullable=True)
    pkgqty = Column(Integer, unique=False, nullable=True)
    vparturl = Column(String, unique=False, nullable=True)

    # Relationships
    vpno_id = Column(Integer,
                     ForeignKey('VendorPartNumber.id'),
                     unique=True, nullable=False, index=True)
    vpno = relationship(
        "VendorPartNumber",
        backref=backref('detail', cascade='all, delete-orphan', uselist=False),
        lazy='joined',
    )


class VendorElnPartDetail(DeclBase, BaseMixin):
    package = Column(String, unique=False, nullable=True)
    datasheet = Column(String, unique=False, nullable=True)

    # Relationships
    vpno_id = Column(Integer,
                     ForeignKey('VendorPartNumber.id'),
                     unique=True, nullable=False, index=True)
    vpno = relationship(
        "VendorPartNumber",
        backref=backref('detail_eln', cascade='all, delete-orphan', uselist=False),
        lazy='joined',
    )


class VendorPrice(DeclBase, BaseMixin, TimestampMixin):
    moq = Column(Integer, unique=False, nullable=False)
    price = Column(String, unique=False, nullable=False)
    oqmultiple = Column(Integer, unique=False, nullable=False)

    # Relationships
    vpno_id = Column(Integer, ForeignKey('VendorPartNumber.id'),
                     unique=False, nullable=False, index=True)
    vpno = relationship(
        "VendorPartNumber",
        backref=backref('prices', cascade='all, delete-orphan'),
        lazy='joined',
    )
