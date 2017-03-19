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
Replay Test Result Script  (``tendril-testresult``)
===================================================

Replays the latest test result for the specified serial number on the
command line.

.. seealso::
    :mod:`tendril.testing.analysis`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.testresult
    :func: _get_parser
    :prog: tendril-testresult
    :nodefault:

"""

import argparse

from tendril.testing import analysis
from tendril.utils.db import get_session
from .helpers import add_base_options


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-testresult script.
    """
    parser = argparse.ArgumentParser(
        description='Replay Latest Test Results',
        prog='tendril-runtest'
    )
    add_base_options(parser)
    parser.add_argument(
        'serialno', metavar='SNO', type=str,
        help='Device serial number'
    )
    return parser


def main():
    """
    The tendril-testresult script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    with get_session() as s:
        suites = analysis.get_test_suite_objects(
                serialno=args.serialno, session=s
        )
        for suite in suites:
            suite.finish()


if __name__ == '__main__':
    main()
