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

import os
from fs.opener import fsopendir
from fs.utils import copyfile
from fs import path

from tendril.utils.db import with_db

from tendril.entityhub import serialnos
from tendril.utils.config import DOCSTORE_ROOT
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.config import REFDOC_ROOT

from tendril.utils.config import DOCUMENT_WALLET_PREFIX
from tendril.utils.config import REFDOC_PREFIX
from tendril.utils.config import DOCSTORE_PREFIX

from db import controller
from wallet import wallet_fs

from tendril.utils import log

logger = log.get_logger(__name__, log.INFO)
docstore_fs = fsopendir(DOCSTORE_ROOT, create_dir=True)
workspace_fs = fsopendir(os.path.join(INSTANCE_ROOT, 'scratch'),
                         create_dir=True)
refdoc_fs = fsopendir(REFDOC_ROOT)
local_fs = fsopendir('/')


class ExposedDocument(object):
    def __init__(self, desc, fspath, fs, ts=None, efield=None):
        self.desc = desc
        self.path = fspath
        self.fs = fs
        self.ts = ts
        self.efield = efield
        self._get_fs_prefix()

    def _get_fs_prefix(self):
        if self.fs == refdoc_fs:
            self._prefix = os.path.join('/expose', REFDOC_PREFIX)
        elif self.fs == docstore_fs:
            self._prefix = os.path.join('/expose', DOCSTORE_PREFIX)
        elif self.fs == wallet_fs:
            self._prefix = os.path.join('/expose', DOCUMENT_WALLET_PREFIX)

    @property
    def exposed_url(self):
        return os.path.join(self._prefix, self.path)

    @property
    def filetype(self):
        ext = os.path.splitext(self.path)[1]
        if not ext:
            return None
        return ext.strip('.').lower()

    @property
    def filename(self):
        return path.splitext(path.split(self.path)[1])[0]


@with_db
def list_sno_documents(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("sno cannot be None")
    results = controller.get_sno_documents(serialno=serialno, session=session)
    print ("Documents for Serial No. : " + serialno)
    for result in results:
        print result


def get_docs_list_for_serialno(serialno):
    # TODO This function can be deprecated
    documents = controller.get_sno_documents(serialno=serialno)
    rval = []
    for document in documents:
        rval.append(ExposedDocument(document.doctype,
                                    document.docpath,
                                    docstore_fs,
                                    document.created_at,
                                    document.efield))
    return rval


def get_docs_list_for_doctype(doctype, limit=None):
    # TODO This function can be deprecated
    documents = controller.get_doctype_documents(doctype=doctype, limit=limit)
    rval = []
    for document in documents:
        rval.append(ExposedDocument(document.doctype,
                                    document.docpath,
                                    docstore_fs,
                                    document.created_at,
                                    document.efield))
    return rval


def get_docs_list_for_sno_doctype(serialno, doctype, limit=None):
    documents = controller.get_serialno_doctype_documents(serialno=serialno,
                                                          doctype=doctype,
                                                          limit=limit)
    rval = []
    for document in documents:
        rval.append(ExposedDocument(document.doctype,
                                    document.docpath,
                                    docstore_fs,
                                    document.created_at,
                                    document.efield))
    return rval


@with_db
def copy_docs_to_workspace(serialno=None, workspace=None,
                           clearws=False, setwsno=True,
                           fs=None, session=None):
    if serialno is None:
        raise AttributeError('serialno cannot be None')
    if fs is None:
        fs = workspace_fs
    if workspace is None:
        workspace = fs.makeopendir('workspace', recursive=True)
    elif workspace.startswith('/'):
        raise ValueError('workspace should be a relative path')
    else:
        workspace = fs.makeopendir(workspace, recursive=True)
    if clearws is True:
        for p in workspace.listdir(dirs_only=True):
            workspace.removedir(p, force=True)
        for p in workspace.listdir(files_only=True):
            workspace.remove(p)
    if setwsno is True:
        with workspace.open('wsno', 'wb') as f:
            f.write(serialno)
    for doc in controller.get_sno_documents(serialno=serialno,
                                            session=session):
        docname = os.path.split(doc.docpath)[1]
        if docname.startswith(serialno):
            if not os.path.splitext(docname)[0] == serialno:
                docname = docname[len(serialno) + 1:]
        copyfile(docstore_fs, doc.docpath, workspace, docname)


@with_db
def delete_document(docpath, session=None):
    deregister_document(docpath=docpath, session=session)
    docstore_fs.remove(docpath)


@with_db
def deregister_document(docpath=None, session=None):
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    controller.deregister_document(docpath=docpath, session=session)


def insert_document(sno, docpath, series):
    fname = os.path.split(docpath)[1]
    if not fname.startswith(sno) and \
            not os.path.splitext(fname)[0].endswith(sno):
        fname = sno + '-' + fname
    if series is None:
        series = serialnos.get_series(sno)
    storepath = path.join(series, fname)
    if not docstore_fs.exists(path.dirname(storepath)):
        docstore_fs.makedir(path.dirname(storepath), recursive=True)
    copyfile(local_fs, docpath, docstore_fs, storepath)
    return storepath


@with_db
def register_document(serialno=None, docpath=None, doctype=None,
                      efield=None, series=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if docpath is None:
        raise AttributeError('docpath cannot be None')
    if doctype is None:
        raise AttributeError('doctype cannot be None')

    logger.info("Registering document for sno " + str(serialno) + " : " +
                str(docpath))
    # WARNING : This writes the file before actually checking that all is ok.
    #           This may not be a very safe approach.
    storepath = insert_document(serialno, docpath, series)
    controller.register_document(serialno=serialno, docpath=storepath,
                                 doctype=doctype, efield=efield,
                                 session=session)


# def clean_docindex():
#     pass
#
#
# def clean_docstore():
#     pass
