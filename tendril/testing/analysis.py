"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import re
import os

from tendril.utils.db import with_db
from tendril.entityhub import serialnos
from tendril.entityhub import projects
from tendril.boms.electronics import import_pcb

from tendril.dox.docstore import register_document
from tendril.entityhub.serialnos import get_series

from tendril.utils.config import PRINTER_NAME


from db import controller
from testbase import TestSuiteBase
from tests import get_test_object

rex_cls = re.compile(ur'^<class \'(?P<cl>[a-zA-Z0-9.]+)\'>$')


@with_db
def get_test_suite_objects(serialno=None, session=None):
    # This reconstructs the test objects from the database. Using SQLAlchemy
    # as the ORM that it is, and letting it handle the object creation would
    # be infinitely better. It isn't done here since the models are separate
    # from the actual test objects, which in turn have other dependencies.
    # Integrating the models with the classes should be considered in the
    # future when there is time.
    suite_names = controller.get_test_suite_names(serialno=serialno,
                                                  session=session)
    devicetype = serialnos.get_serialno_efield(sno=serialno, session=session)
    projectfolder = projects.cards[devicetype]
    bomobj = import_pcb(cardfolder=projectfolder)
    # Perhaps this bomobject should not be recreated on the fly.
    bomobj.configure_motifs(devicetype)

    suites = []

    for suite_name in suite_names:
        suite_db_obj = controller.get_latest_test_suite(serialno=serialno,
                                                        suite_class=suite_name,
                                                        session=session)
        if suite_db_obj.suite_class == "<class 'tendril.testing.testbase.TestSuiteBase'>":
            suite_obj = TestSuiteBase()
        else:
            raise ValueError("Unrecognized suite_class : " + suite_db_obj.suite_class)

        suite_obj.desc = suite_db_obj.desc
        suite_obj.title = suite_db_obj.title
        suite_obj.ts = suite_db_obj.created_at
        suite_obj.serialno = serialno

        for test_db_obj in suite_db_obj.tests:
            cls_name = rex_cls.match(test_db_obj.test_class).group('cl')
            test_obj = get_test_object(cls_name, offline=True)
            test_obj.desc = test_db_obj.desc
            test_obj.title = test_db_obj.title
            test_obj.ts = test_db_obj.created_at
            test_obj.use_bom(bomobj)
            test_obj.load_result_from_obj(test_db_obj.result)
            suite_obj.add_test(test_obj)
            # Crosscheck test passed?

        # Crosscheck suite passed?

        suites.append(suite_obj)

    return suites


def publish_and_print(serialno, devicetype, print_to_paper=False):
    from tendril.dox import testing
    pdfpath = testing.render_test_report(serialno=serialno)
    register_document(serialno, docpath=pdfpath, doctype='TEST-RESULT',
                      efield=devicetype, series='TEST/' + get_series(sno=serialno))
    if print_to_paper:
        os.system('lp -d {1} -o media=a4 {0}'.format(pdfpath, PRINTER_NAME))
