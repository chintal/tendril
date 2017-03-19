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
Workspace / Document Retrieval Script (``tendril-getdox``)
==========================================================

This script retrieves all the documents in the docstore related
to a linked to the specified serial number and populates the
provided workspace folder with them.

This script can be used to regenerate the context from which an
order can be regenerated using the appropriate script.

.. seealso::
    :mod:`tendril.dox.docstore.copy_dox_to_workspace`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.getdox
    :func: _get_parser
    :prog: tendril-getdox
    :nodefault:

"""


import argparse
from .helpers import add_base_options

from tendril.dox import docstore
from tendril.utils import log
logger = log.get_logger("getdox", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-getdox script.
    """
    parser = argparse.ArgumentParser(
        description='Copy published documents into the workspace.',
        prog='tendril-getdox'
    )
    add_base_options(parser)
    parser.add_argument(
        'serialno', metavar='SNO', type=str, nargs='?',
        help='Document serial number'
    )
    parser.add_argument(
        '--workspace', '-w', metavar=('NAME'), type=str, nargs=1,
        help="The name of the workspace to use. Default 'workspace'. "
             "The folder is relative to the instance workspace, " +
             "$HOME/.tendril/scratch/"
    )
    parser.add_argument(
        '--clear-ws', '-c', action='store_true', default=False,
        help="Remove any files already present in the workspace. "
    )
    return parser


def main():
    """
    The tendril-getdox script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    if not args.serialno:
        parser.print_help()
        exit()
    docstore.copy_docs_to_workspace(serialno=args.serialno,
                                    workspace=args.workspace,
                                    clearws=args.clear_ws,
                                    )


if __name__ == '__main__':
    main()
