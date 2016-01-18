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

import idstring

from tendril.utils.db import with_db

from db import controller
from sqlalchemy.orm.exc import NoResultFound

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


@with_db
def get_serialno_object(sno=None, session=None):
    return controller.get_serialno_object(sno=sno, session=session)


@with_db
def get_serialno_efield(sno=None, session=None):
    return controller.get_serialno_object(sno=sno, session=session).efield


@with_db
def set_serialno_efield(sno=None, efield=None, session=None):
    sobj = controller.get_serialno_object(sno=sno, session=session)
    sobj.efield = efield
    return


@with_db
def serialno_exists(sno=None, session=None):
    try:
        controller.get_serialno_object(sno=sno, session=session)
        return True
    except (NoResultFound, controller.SerialNoNotFound):
        return False


@with_db
def register_serialno(sno=None, efield=None, session=None):
    logger.info("Registering new serial number : " + sno)
    return controller.register_serialno(sno=sno, efield=efield,
                                        session=session)


@with_db
def link_serialno(child=None, parent=None, association_type=None,
                  verbose=True, session=None):
    if child is None:
        raise AttributeError("child cannot be None")
    if parent is None:
        raise AttributeError("parent cannot be None")
    if verbose:
        print("Linking " + child + " to parent " + parent)
    return controller.link_serialno(child=child, parent=parent,
                                    association_type=association_type,
                                    session=session)


@with_db
def get_parent_serialnos(sno=None, session=None):
    if sno is None:
        raise AttributeError("child cannot be None")
    return controller.get_serialno_object(
        sno=sno, session=session).parents


@with_db
def get_child_serialnos(sno=None, session=None):
    if sno is None:
        raise AttributeError("child cannot be None")
    return controller.get_child_snos(serialno=sno, session=session)


@with_db
def delete_serialno(sno, recurse=False, session=None):
    if recurse is True:
        for snoi in get_child_serialnos(sno):
            controller.delete_serialno(snoi, recurse, session)
    controller.delete_serialno(sno, recurse, session)


# def delete_series(series):
#     for serialno in get_all_serialnos():
#         if get_series(serialno) == series:
#             logger.info("Deleting Serial No : " + serialno)
#             delete_serialno(serialno)
#     logger.info("Deleting Series : " + series)
#     nsno_table.delete(series=series)


def create_serial_series(series, start_seed, description):
    if isinstance(series, unicode):
        series = series.encode('ascii', 'replace')
    if isinstance(start_seed, unicode):
        start_seed = start_seed.encode('ascii', 'replace')
    if isinstance(description, unicode):
        description = description.encode('ascii', 'replace')
    return controller.create_series_obj(
        series=series, start_seed=start_seed, description=description)


def get_series(sno):
    return sno.split('-')[0]


def get_number(sno):
    return sno.split('-')[1]


@with_db
def get_all_series(session=None):
    return controller.get_series_obj(session=session)


@with_db
def get_serialno(series=None, efield=None, register=True,
                 start_seed='100A', create_series=False, session=None):
    series = series.upper()
    try:
        series_obj = controller.get_series_obj(series=series, session=session)
    except controller.SeriesNotFound:
        if not create_series:
            raise
        series_obj = None
    if series_obj is not None:
        last_seed = series_obj.last_seed
        logger.debug("Found last seed for series " + str(series) +
                     " : " + str(last_seed))
        generator = idstring.IDstring(seed=last_seed)
        new_sno = generator + 1
        if register is True:
            logger.debug("Updating seed for series " + series +
                         " : " + str(new_sno.get_seed()))
            series_obj.last_seed = new_sno.get_seed()
            register_serialno(
                sno=series + '-' + new_sno,
                efield=efield, session=session
            )
        else:
            logger.info("Not updating seed for series " + series +
                        " : " + str(new_sno.get_seed()))
        return series + '-' + new_sno
    else:
        logger.info("Could not find series in db : " + series)
        generator = idstring.IDstring(seed=start_seed)
        if register is True:
            logger.info("Creating series in db : " + series)
            controller.create_series_obj(
                series=series, start_seed=start_seed, session=session
            )
            register_serialno(
                sno=series + '-' + generator,
                efield=efield, session=session
            )
        else:
            logger.info("NOT Creating series in db : " + series)
        return series + '-' + generator
