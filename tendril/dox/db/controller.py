#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for controller
"""

from sqlalchemy.orm.exc import NoResultFound
from tendril.utils.db import with_db
from tendril.entityhub.db.model import SerialNumber
from tendril.entityhub import serialnos

from sqlalchemy import desc
from model import DocStoreDocument

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


@with_db
def get_sno_documents(serialno=None, session=None):
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno, session=session)
    return session.query(DocStoreDocument).filter_by(serialno=serialno).all()


@with_db
def get_doctype_documents(doctype=None, limit=None, session=None):
    q = session.query(DocStoreDocument).filter(
        DocStoreDocument.doctype == doctype
    )
    q = q.order_by(desc(DocStoreDocument.created_at))
    if limit:
        q = q.limit(limit)
    return q.all()


@with_db
def get_serialno_doctype_documents(serialno=None, doctype=None,
                                   limit=None, session=None):
    q = session.query(DocStoreDocument)
    if serialno is not None:
        if not isinstance(serialno, SerialNumber):
            serialno = serialnos.get_serialno_object(sno=serialno,
                                                     session=session)
        q = q.filter_by(serialno=serialno)
    if doctype:
        q = q.filter(DocStoreDocument.doctype == doctype)

    q = q.order_by(desc(DocStoreDocument.created_at))
    if limit:
        q = q.limit(limit)
    return q.all()


@with_db
def get_snos_by_document_doctype(doctype=None, series=None,
                                 limit=None, session=None):
    if doctype is None:
        raise AttributeError("doctype cannot be None")
    if series is not None and not isinstance(series, str):
        raise AttributeError('series must be a string or None')

    q = session.query(SerialNumber)
    if series is not None:
        q = q.filter(SerialNumber.sno.like('{0}%'.format(series)))

    q = q.join(DocStoreDocument.serialno)
    q = q.filter(DocStoreDocument.doctype == doctype)
    q = q.order_by(desc(SerialNumber.created_at))

    if limit is not None:
        q.limit(limit)

    return q.all()


@with_db
def register_document(serialno=None, docpath=None, doctype=None,
                      efield=None, clobber=True, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if doctype is None:
        raise AttributeError('doctype cannot be None')

    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)

    try:
        q = session.query(DocStoreDocument).filter_by(
            serialno=serialno, docpath=docpath
        )
        existing = q.one()
    except NoResultFound:
        # default does not exist yet, so add it...
        session.add(
            DocStoreDocument(docpath=docpath, doctype=doctype,
                             efield=efield, serialno_id=serialno.id,
                             serialno=serialno)
        )
    else:
        if clobber is True:
            existing.serialno = serialno
            existing.doctype = doctype
            existing.docpath = docpath
            existing.efield = efield
            session.add(existing)
        else:
            raise ValueError("Document already exists, and clobber is False")


@with_db
def deregister_document(docpath=None, session=None):
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if not isinstance(docpath, DocStoreDocument):
        docpath = session.query(
            DocStoreDocument).filter_by(docpath=docpath).one()
    session.delete(docpath)
    session.flush()
