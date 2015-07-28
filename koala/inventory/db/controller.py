"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

import koala.utils.db
from model import InventoryLocationCode

from koala.utils.config import INVENTORY_LOCATIONS


def get_inventorylocationcode(name, create=False):
    with koala.utils.db.get_session() as session:
        try:
            return session.query(InventoryLocationCode).filter_by(name=name).one().id
        except MultipleResultsFound:
            logger.warning("Found Multiple Codes for Inventory Location : " + name)
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
        with koala.utils.db.get_session() as session:
            if not session.query(exists().where(InventoryLocationCode.name == location)).scalar():
                logger.info("Creating location code for : " + location)
                obj = InventoryLocationCode(name=location)
                session.add(obj)
            else:
                logger.debug("Found preexisting location code for : " + location)
