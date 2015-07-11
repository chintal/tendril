"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import datetime
import pytz
import os
import shutil
import glob

import utils.state
from utils.config import DOCSTORE_ROOT
from utils.config import INSTANCE_ROOT

snodoc_table = utils.state.state_ds['snodoc']


class DocumentBase(object):
    def __init__(self, doctype, docpath, timestamp, efield):
        self.doctype = doctype
        self.docpath = docpath
        self.timestamp = timestamp
        self.efield = efield

    @property
    def sno(self):
        results = snodoc_table.find(docpath=self.docpath)
        rval = []
        for result in results:
            rval.append(result['sno'])
        return rval

    def __repr__(self):
        return '{0:<35} {1:<20} {3:<25} {2:<40} '.format(str(self.timestamp), str(self.doctype), str(self.docpath), str(self.efield))


def list_sno_documents(sno):
    results = get_sno_documents(sno)
    print ("Documents for Serial No. : " + sno)
    for result in results:
        print result


def get_sno_documents(sno):
    if sno == '*':
        results = snodoc_table.find()
    else:
        results = snodoc_table.find(sno=sno)
    rval = []
    for result in results:
        rval.append(DocumentBase(result['doctype'], result['docpath'], result['timestamp'], result['efield']))
    return rval


def copy_docs_to_workspace(sno, workspace=None, clearws=False, setwsno=True, iagree=False):
    if workspace is None:
        workspace = os.path.join(INSTANCE_ROOT, 'scratch', 'workspace')
    elif workspace.startswith('/'):
        workspace = workspace
        if clearws is True and iagree is False:
            raise StandardError('Workspace defined outside the Instance Scratch Area, and clearws is set to True. '
                                'All files within the provided path will be removed. '
                                'Set the iagree argument to True to accept responsibility for what you\'re doing.')
    else:
        workspace = os.path.join(INSTANCE_ROOT, 'scratch', 'customs')
    if clearws is True:
        glb = os.path.join(workspace, '*')
        rf = glob.glob(glb)
        for f in rf:
            os.remove(f)
    if setwsno is True:
        with open(os.path.join(workspace, 'wsno'), 'w') as f:
            f.write(sno)
    for doc in get_sno_documents(sno):
        docname = os.path.split(doc.docpath)[1]
        if docname.startswith(sno):
            docname = docname[len(sno)+1:]
        shutil.copy(os.path.join(DOCSTORE_ROOT, doc.docpath),
                    os.path.join(workspace, docname))


def delete_document(docpath):
    deregister_document(docpath, sno='*')
    os.remove(os.path.join(DOCSTORE_ROOT, docpath))


def deregister_document(docpath, sno=None):
    if sno is None:
        raise ValueError("Specify serial number or '*' for all")
    elif sno == '*':
        snodoc_table.delete(docpath=docpath)
    else:
        snodoc_table.delete(docpath=docpath, sno=sno)


def insert_document(sno, docpath, series):
    fname = os.path.split(docpath)[1]
    if not fname.startswith(sno) and not os.path.splitext(fname)[0].endswith(sno):
        fname = sno + '-' + fname
    storepath = os.path.join(DOCSTORE_ROOT, series.replace('/', os.path.sep), fname)
    if not os.path.exists(os.path.dirname(storepath)):
        os.makedirs(os.path.dirname(storepath))
    shutil.copyfile(docpath, storepath)
    return storepath


def register_document(sno, docpath, doctype, efield=None, series=None):
    logger.info("Registering document for sno " + str(sno) + " : " + str(docpath))
    storepath = insert_document(sno, docpath, series)
    storepath = os.path.relpath(storepath, DOCSTORE_ROOT)
    snodoc_table.upsert(dict(sno=sno, docpath=storepath, doctype=doctype, efield=efield,
                             timestamp=pytz.UTC.localize(datetime.datetime.now()).isoformat()),
                        keys=['sno', 'docpath'])


def clean_docindex():
    pass


def clean_docstore():
    pass
