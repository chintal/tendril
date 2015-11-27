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

import argparse

from tendril.dox import docstore
from tendril.utils import log
logger = log.get_logger("getdox", log.DEFAULT)


def main():
    parser = argparse.ArgumentParser(
        description='Copy published documents into the workspace.',
        prog='tendril-getdox'
    )
    parser.add_argument(
        'serialno', metavar='SNO', type=str, nargs='?',
        help='Document serial number'
    )
    parser.add_argument(
        '--workspace', '-w', metavar=('NAME'), type=str, nargs=1,
        help="The name of the workspace to use. Default 'workspace'. "
             "The folder is relative to the instance workspace, " +
             docstore.workspace_fs.getsyspath('/')
    )
    parser.add_argument(
        '--clear-ws', '-c', action='store_true', default=False,
        help="Remove any files already present in the workspace. "
    )

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
