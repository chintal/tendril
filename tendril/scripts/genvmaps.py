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
Vendor Map Generation Script (``tendril-genvmaps``)
===================================================

This script generates vendor maps for all recognized components in the
library.

.. warning::
    This script retrieves information from vendors. It will
    take some time to execute.

.. seealso::
    :mod:`tendril.sourcing.electronics.gen_vendor_mapfile`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.genvmaps
    :func: _get_parser
    :prog: tendril-genvmaps
    :nodefault:

"""

import argparse
from .helpers import add_vendor_selection_options
from .helpers import add_base_options


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-genvmaps script.
    """
    parser = argparse.ArgumentParser(
        description='(Re)generate vendor maps.',
        prog='tendril-genvmap'
    )
    add_base_options(parser)
    add_vendor_selection_options(parser)
    parser.add_argument(
        '--force', '-f', action='store_true', default=False,
        help='Regenerate mapfile for all idents, even if is not stale.'
    )
    parser.add_argument(
        '--lazy', '-l', action='store_true', default=False,
        help="Don't regenerate mapfile for idents which exist, "
             "even if it is stale."
    )
    return parser


def run(vobj=None, force=False, lazy=False):
    """
    Generates vendor maps for the provided vendor.

    :param vobj: Vendor to generate the map for, or None for all.

    """
    from tendril.sourcing.map import gen_vendor_mapfile
    from tendril.sourcing.electronics import vendor_list

    maxage = -1

    if force is True:
        maxage = 0

    if lazy is True:
        maxage = -1

    if not vobj:
        for v in vendor_list:
            gen_vendor_mapfile(v, maxage)
    else:
        gen_vendor_mapfile(vobj, maxage)


def main():
    """
    The tendril-genvmaps script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    if args.all:
        run(force=args.force, lazy=args.lazy)
        return

    if not args.vendor_name:
        parser.print_help()
        return

    from tendril.sourcing.electronics import get_vendor_by_name
    from tendril.sourcing.electronics import vendor_list
    v = get_vendor_by_name(args.vendor_name)
    if not v:
        parser.print_help()
        print("")
        print("recognized vendors: ")

        for v in vendor_list:
            print("  {0:<20} {1}".format(v._name, v.name))
        return

    run(v, args.force, args.lazy)


if __name__ == '__main__':
    main()
