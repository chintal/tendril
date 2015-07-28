"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
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
    return create_engine(DB_URI)

engine = init_db_engine()

Session = sessionmaker()
Session.configure(bind=engine)


@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class BaseMixin(object):
    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    # __table_args__ = {'mysql_engine': 'InnoDB'}
    # __mapper_args__= {'always_refresh': True}

    id = Column(Integer, primary_key=True)

DeclBase = declarative_base()


class TimestampMixin(object):
    created_at = Column(DateTime, default=datetime.now())


def commit_metadata():
    DeclBase.metadata.create_all(engine)
