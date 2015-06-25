"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import datetime
import pytz
import idstring

import utils.state

sno_table = utils.state.state_ds['sno']
snodoc_table = utils.state.state_ds['snodoc']


def list_all(doctype='REGISTER'):
    results = snodoc_table.find(doctype=doctype)
    for result in results:
        if result is not None:
            print list_documents(result['sno'])


def list_documents(sno):
    results = snodoc_table.find(sno=sno)
    print ("Documents for Serial No. : " + sno)
    for result in results:
        print '{0:<40} {1:<10} {3:<20} {2:<40} '.format(str(result['timestamp']), str(result['doctype']), str(result['docpath']), str(result['efield']))


def register_document(sno, docpath, doctype, efield=None):
    logger.info("Registering document for sno " + str(sno) + " : " + str(docpath))
    snodoc_table.insert(dict(sno=sno, docpath=docpath, doctype=doctype, efield=efield,
                             timestamp=pytz.UTC.localize(datetime.datetime.now()).isoformat()))


def get_serialno(series, efield=None, register=True, start_seed='100A'):
    series = series.upper()
    if series in [x['series'] for x in sno_table]:
        last_seed = sno_table.find_one(series=series)['last_seed']
        logger.debug("Found last seed for series " + str(series) + " : " + str(last_seed))
        generator = idstring.IDstring(seed=last_seed)
        new_sno = generator + 1
        if register is True:
            logger.info("Updating seed for series " + series + " : " + str(new_sno.get_seed()))
            sno_table.update(dict(series=series, last_seed=new_sno.get_seed()), ['series'])
            register_document(series + '-' + new_sno, None, "REGISTER", efield)
        else:
            logger.info("Not updating seed for series " + series + " : " + str(new_sno.get_seed()))
        return series + '-' + new_sno
    else:
        logger.info("Could not find series in db : " + series)
        generator = idstring.IDstring(seed=start_seed)
        if register is True:
            logger.info("Creating series in db : " + series)
            sno_table.insert(dict(series=series, last_seed=start_seed))
            register_document(series + '-' + generator, None, "REGISTER", efield)
        else:
            logger.info("NOT Creating series in db : " + series)
        return series + '-' + generator
