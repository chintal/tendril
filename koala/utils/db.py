# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Koala.
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
The Database Utils Module (:mod:`koala.utils.db`)
=================================================

This module provides utilities to deal with Koala's Database. While the actual
functionality is provided by the :mod:`sqlalchemy` package, the contents of
this utility module simplify and specify the application code's interaction
with :mod:`sqlalchemy`

.. rubric:: Module Contents

"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, Integer, DateTime


log.logging.getLogger('sqlalchemy.engine').setLevel(log.WARNING)

from contextlib import contextmanager
from datetime import datetime

from koala.utils.config import DB_URI


def init_db_engine():
    """
    Initializes the database engine and binds it to the Database URI
    defined by the :mod:`koala.utils.config` module.

    This function is called within the module and an engine is readily
    available in the module variable :data:`koala.utils.db.engine`. Application
    code should not have to create a new engine for the normal use cases.
    """
    return create_engine(DB_URI)

#: The :class:`sqlalchemy.Engine` object
engine = init_db_engine()

#: The :class:`sqlalchemy.sessionmaker` bound to the database engine
Session = sessionmaker(expire_on_commit=False)
Session.configure(bind=engine)


@contextmanager
def get_session():
    """
    Application executable code will typically only have to interact with this
    ``contextmanager``. It should use this to create a database session,
    perform its tasks, whatever they may be, within this contex, and then
    exit the context.
    """
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def with_db(func):
    def inner(session=None, **kwargs):
        if session is None:
            with get_session() as s:
                return func(session=s, **kwargs)
        else:
            return func(session=session, **kwargs)
    return inner


class BaseMixin(object):
    """
    This Mixin can / should be used (by inheriting from) by all Model classes
    defined by application code. It defines the :attr:`__tablename__` attribute
    of the Model class to the name of the class and creates a Primary Key Column
    named id in the table for the Model.
    """
    @declared_attr
    def __tablename__(self):
        return self.__name__

    # __table_args__ = {'mysql_engine': 'InnoDB'}
    # __mapper_args__= {'always_refresh': True}

    id = Column(Integer, primary_key=True)


#: The :mod:`sqlalchemy` declarative base for all Model defined by / in Koala
DeclBase = declarative_base()


class TimestampMixin(object):
    """
    This Mixin can be used by any Models which require a timestamp to be
    created. It adds a column named ``created_at``, which defauts to the
    time at which the object is instantiated.
    """
    created_at = Column(DateTime, default=datetime.now())


def commit_metadata():
    """
    This function commits all metadata to the table. This function should be
    run after importing **all** the Model classes, and it will create the
    tables in the database.
    """
    from koala.entityhub.db import model
    from koala.inventory.db import model
    from koala.dox.db import model
    from koala.testing.db import model

    DeclBase.metadata.create_all(engine)
