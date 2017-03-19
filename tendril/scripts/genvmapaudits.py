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
from .helpers import add_base_options


def run(vobj=None, force=False, lazy=False):
    from tendril.sourcing.map import export_vendor_map_audit
    from tendril.sourcing.electronics import vendor_list

    maxage = -1

    if force is True:
        maxage = 0

    if lazy is True:
        maxage = -1

    if not vobj:
        for v in vendor_list:
            export_vendor_map_audit(v, maxage)
    else:
        export_vendor_map_audit(vobj, maxage)


def main():
    parser = argparse.ArgumentParser(
        description='(Re)generate vendor map audits.',
        prog='tendril-genvmapaudit'
    )
    add_base_options(parser)
    parser.add_argument(
        'vendor_name', metavar='VENDOR_NAME', type=str, nargs='?',
        help='Name of the vendor.'
    )
    parser.add_argument(
        '--all', '-a', action='store_true', default=False,
        help='Run for all vendors. If used, will ignore VENDOR_NAME.'
    )
    parser.add_argument(
        '--force', '-f', action='store_true', default=False,
        help='Regenerate for all parts, even if they are not stale.'
    )
    parser.add_argument(
        '--lazy', '-l', action='store_true', default=False,
        help="Don't regenerate for parts which exist, even if they are stale."
    )

    args = parser.parse_args()
    if args.all:
        run(force=args.force)
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
            print("  {0:<20} {1}".format(v.cname, v.name))
        return

    run(v, args.force, args.lazy)


if __name__ == '__main__':
    main()
