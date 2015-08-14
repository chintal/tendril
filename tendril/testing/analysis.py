"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import re

from tendril.utils.db import with_db

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

        for test_db_obj in suite_db_obj.tests:
            cls_name = rex_cls.match(test_db_obj.test_class).group('cl')
            test_obj = get_test_object(cls_name, offline=True)
            test_obj.desc = test_db_obj.desc
            test_obj.title = test_db_obj.title
            test_obj.ts = test_db_obj.created_at
            test_obj.load_result_from_obj(test_db_obj.result)
            # Crosscheck test passed?

        # Crosscheck suite passed?

        suites.append(suite_obj)

    return suites
