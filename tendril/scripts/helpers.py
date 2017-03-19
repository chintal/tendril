#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
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
Script Helpers
==============

Small functions to help simplify and streamline script creation.

"""

import os


def get_project_folder(projectfolder):
    if os.path.split(projectfolder)[1] == 'configs.yaml':
        projectfolder = os.path.split(projectfolder)[0]
    if os.path.split(projectfolder)[1] == 'schematic':
        projectfolder = os.path.split(projectfolder)[0]
    return projectfolder


def add_base_options(parser):
    import tendril
    ver = 'tendril {0}'.format(tendril.__version__)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ({0})'.format(ver))


def add_project_selector_options(parser):
    """
    Add arguments for project selection to the provided
    parser.

    The following arguments are added :

        - ``projfolders``
        - ``recurse``
        - ``all``

    :param parser: The parser to add the arguments to.
    :type parser: :class:`argparse.ArgumentParser`

    """
    parser.add_argument(
        'projfolders', metavar='PATH', type=str, nargs='*',
        help='gEDA Project Folder(s), ignored for --all.'
    )
    parser.add_argument(
        '--recurse', '-r', action='store_true', default=False,
        help='Recursively search for projects under each provided PATH.'
    )
    parser.add_argument(
        '--all', '-a', action='store_true', default=False,
        help='All recognized projects.'
    )
    parser.add_argument(
        '--include-suspended', '-iu', dest='statuses', action='append_const',
        const='Suspended', help='Include suspended projects.'
    )
    parser.add_argument(
        '--include-deprecated', '-ip', dest='statuses', action='append_const',
        const='Deprecated', help='Include deprecated projects.'
    )
    parser.add_argument(
        '--include-archived', '-ir', dest='statuses', action='append_const',
        const='Archived', help='Include archived projects.'
    )
    parser.add_argument(
        '--include-discarded', '-is', dest='statuses', action='append_const',
        const='Discarded', help='Include discarded projects.'
    )


def add_module_selector_options(parser):
    parser.add_argument(
        '--modules', '-m', metavar='MODULE', type=str, nargs='*',
        help='Module Names. Overrides any PATHs that may be provided.'
    )
    add_project_selector_options(parser)


def add_vendor_selection_options(parser):
    """
    Add arguments for vendor selection to the provided
    parser.

    The following arguments are added :

        - ``vendor_name``
        - ``all``

    :param parser: The parser to add the arguments to.
    :type parser: :class:`argparse.ArgumentParser`

    """

    parser.add_argument(
        'vendor_name', metavar='VENDOR_NAME', type=str, nargs='?',
        help='Name of the vendor. Ignored for --all.'
    )
    parser.add_argument(
        '--all', '-a', action='store_true', default=False,
        help='Run for all vendors.'
    )
