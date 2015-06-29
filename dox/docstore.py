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

import utils.state

from utils.config import DOCSTORE_ROOT

snodoc_table = utils.state.state_ds['snodoc']


def list_documents(sno):
    results = snodoc_table.find(sno=sno)
    print ("Documents for Serial No. : " + sno)
    for result in results:
        print '{0:<35} {1:<20} {3:<25} {2:<40} '.format(str(result['timestamp']), str(result['doctype']), str(result['docpath']), str(result['efield']))


def insert_document(sno, docpath, series):
    fname = os.path.split(docpath)[1]
    storepath = os.path.join(DOCSTORE_ROOT, series, sno + '-' + fname)
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
