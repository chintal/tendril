"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import idstring

import utils.state


sno_table = utils.state.state_ds['sno']
nsno_table = utils.state.state_ds['nsno']
snodoc_table = utils.state.state_ds['snodoc']


def get_sno_efield(sno):
    results = sno_table.find_one(sno=sno)
    return results['efield']


def get_all_serialnos():
    results = sno_table.find()
    for result in results:
        yield result['sno']


def list_all_serialnos():
    results = sno_table.find()
    for result in results:
        print result['sno'] + ' :  ' + str(result['efield']) + ' : ' + str(result['parent'])


def serialno_exists(serial):
    results = sno_table.find(sno=serial)
    if len(results) > 0:
        if len(results) > 1:
            logger.warning("Possible duplicate sno : " + serial)
        return True


def register_serialno(sno, efield=None, parent=None):
    logger.info("Registering new serial number : " + sno)
    sno_table.upsert(dict(sno=sno, efield=efield, parent=parent), keys=['sno'])


def get_series(sno):
    return sno.split('-')[0]


def delete_series(series):
    for serialno in get_all_serialnos():
        if get_series(serialno) == series:
            logger.info("Deleting Serial No : " + serialno)
            delete_serialno(serialno)
    logger.info("Deleting Series : " + series)
    nsno_table.delete(series=series)


def delete_serialno(sno, recurse=False, docs=False):
    if recurse is True:
        for sno in get_child_serialnos(sno):
            delete_serialno(sno, True, docs)
    if docs is True:
        import dox.docstore
        for document in dox.docstore.get_sno_documents(sno):
            dox.docstore.delete_document(document)
    sno_table.delete(sno=sno)


def link_serialno(child, parent):
    logger.info("Linking " + child + " to parent " + parent)
    sno_table.update(dict(sno=child, parent=parent), keys=['sno'])


def get_parent_serialno(sno):
    results = sno_table.find(sno=sno)
    if len(results) == 0:
        return None
    return results[0]['parent']


def get_child_serialnos(sno):
    results = sno_table.find(parent=sno)
    return [x['sno'] for x in results]


def get_serialno(series, efield=None, register=True, start_seed='100A'):
    series = series.upper()
    if series in [x['series'] for x in nsno_table]:
        last_seed = nsno_table.find_one(series=series)['last_seed']
        logger.debug("Found last seed for series " + str(series) + " : " + str(last_seed))
        generator = idstring.IDstring(seed=last_seed)
        new_sno = generator + 1
        if register is True:
            logger.info("Updating seed for series " + series + " : " + str(new_sno.get_seed()))
            nsno_table.update(dict(series=series, last_seed=new_sno.get_seed()), ['series'])
            register_serialno(series + '-' + new_sno, efield)
        else:
            logger.info("Not updating seed for series " + series + " : " + str(new_sno.get_seed()))
        return series + '-' + new_sno
    else:
        logger.info("Could not find series in db : " + series)
        generator = idstring.IDstring(seed=start_seed)
        if register is True:
            logger.info("Creating series in db : " + series)
            nsno_table.insert(dict(series=series, last_seed=start_seed))
            register_serialno(series + '-' + generator, efield)
        else:
            logger.info("NOT Creating series in db : " + series)
        return series + '-' + generator
