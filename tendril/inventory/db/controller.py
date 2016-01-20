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

from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from tendril.utils.db import with_db
from tendril.utils.db import get_session

from tendril.entityhub import serialnos
from tendril.entityhub.db.model import SerialNumber
from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.entityhub.entitybase import EntityNotFound
from tendril.auth.db.controller import get_user_object

from .model import InventoryIndent
from .model import InventoryLocationCode

from tendril.utils.config import INVENTORY_LOCATIONS

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class IndentNotFound(EntityNotFound):
    pass


@with_db
def get_inventory_indent(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        try:
            serialno = serialnos.get_serialno_object(sno=serialno,
                                                     session=session)
        except SerialNoNotFound:
            raise IndentNotFound
    try:
        return session.query(InventoryIndent).filter_by(serialno=serialno).one()
    except NoResultFound:
        raise IndentNotFound


@with_db
def upsert_inventory_indent(serialno=None, title=None, desc=None, itype=None,
                            requested_by=None, rdate=None, auth_parent_sno=None,
                            session=None):
    if serialno is not None:
        try:
            inv_obj = get_inventory_indent(serialno=serialno, session=session)
        except IndentNotFound:
            try:
                sno = serialnos.controller.get_serialno_object(
                    sno=serialno, session=session
                )
            except SerialNoNotFound:
                raise AttributeError("Serial number must be preregistered")
            inv_obj = InventoryIndent()
            inv_obj.serialno_id = sno.id
    else:
        raise AttributeError('Serial number must be defined.')
    inv_obj.title = title
    inv_obj.desc = desc
    inv_obj.type = itype
    inv_obj.created_at = rdate

    inv_obj.requested_by = get_user_object(username=requested_by,
                                           session=session)
    inv_obj.auth_parent_id = serialnos.controller.get_serialno_object(
            sno=auth_parent_sno, session=session
    ).id
    session.add(inv_obj)
    session.flush()


def get_inventorylocationcode(name, create=False):
    with get_session() as session:
        try:
            return session.query(
                InventoryLocationCode).filter_by(name=name).one().id
        except MultipleResultsFound:
            logger.warning("Found Multiple Codes for Inventory Location : " +
                           name)
        except NoResultFound:
            if create is True:
                obj = InventoryLocationCode(name=name)
                session.add(obj)
                return obj.id
            else:
                return None


def populate_inventorylocationcodes():
    logger.info("Populating Inventory Location Codes")
    for location in INVENTORY_LOCATIONS:
        with get_session() as session:
            if not session.query(
                    exists().where(
                        InventoryLocationCode.name == location)
            ).scalar():
                logger.info("Creating location code for : " + location)
                obj = InventoryLocationCode(name=location)
                session.add(obj)
            else:
                logger.debug("Found preexisting location code for : " +
                             location)
