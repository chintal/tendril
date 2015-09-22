"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""


import sys

from tendril.testing import analysis
from tendril.utils.db import get_session


def main(serialno=None):
    with get_session() as s:
        suites = analysis.get_test_suite_objects(serialno=serialno, session=s)
        for suite in suites:
            suite.finish()


if __name__ == '__main__':
    main(serialno=sys.argv[1])
