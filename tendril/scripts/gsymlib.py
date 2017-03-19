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
gEDA Symbol Library Search Script  (``tendril-gsymlib``)
========================================================

Simple search tools for searching the gEDA symbol library.

.. seealso::
    :mod:`tendril.gedaif.gsymlib`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.gsymlib
    :func: _get_parser
    :prog: tendril-gedaif
    :nodefault:

"""

import re
import argparse

from tendril.gedaif import gsymlib
from tendril.entityhub import supersets
from tendril.conventions.status import Status

from .helpers import add_base_options

from colorama import Style
from tendril.utils import terminal
from tendril.utils import log
logger = log.get_logger("gsymlib", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-gedaif script.
    """
    parser = argparse.ArgumentParser(
        description='Simple search tools for searching the gEDA '
                    'symbol library.',
        prog='tendril-gedaif'
    )
    add_base_options(parser)
    parser.add_argument(
        '-s', '--search', metavar='SEARCH STRING', type=str,
        help='Search string.'
    )
    parser.add_argument(
        '-x', '--regex', action='store_true', default=False,
        help='The search string is a python regular expression.'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='Print detailed symbol information.'
    )
    parser.add_argument(
        '-u', '--utilization', action='store_true', default=False,
        help='Print symbol utilization information.'
    )
    parser.add_argument(
        '-p', '--pricing', action='store_true', default=False,
        help='Print symbol pricing information. Provides pricing for the '
             'lowest guideline compliant quantity unless otherwise specified '
             'using -q.'
    )
    parser.add_argument(
        '-q', '--quantity', action='store', default=1, type=int,
        help='Retrieve information for a different quantity.'
    )
    return parser


def render_symbol(symbol, verbose=False, inclusion=False, pricing=False):
    width = terminal.get_terminal_width()
    symformat = "{0:<" + str(width - 13) + "} {1:>2}"
    if inclusion or pricing:
        verbose = True
    if not verbose:
        print(symformat.format(symbol.ident,
                               Status(symbol.status).terminal_repr))
        return
    title = symformat.format(symbol.ident,
                             Status(symbol.status).terminal_repr)
    print(Style.BRIGHT + title + Style.NORMAL)
    detailformat = "{0:<15} {1}"
    print(detailformat.format('Description', symbol.description))
    if symbol.datasheet_url:
        print(detailformat.format('Datasheet', symbol.datasheet_url))
    print(detailformat.format('Path', symbol.fpath))
    if pricing:
        if pricing == 1:
            isinfos = symbol.indicative_sourcing_info
        else:
            isinfos = symbol.sourcing_info_qty(pricing)
        print(Style.BRIGHT + "Sources" + Style.NORMAL)
        if not len(isinfos):
            print("--- No known sources of this component ---")
        else:
            isiformat = "{0:30} {1:40} {2:6} (@{3})"
            for isinfo in isinfos:
                print(isiformat.format(isinfo.vobj.name,
                                       isinfo.vpart.vpno,
                                       isinfo.effprice.unit_price,
                                       isinfo.effprice.moq))
    if inclusion:
        inclformat = "{0:<22} {1:6} {2:" + str(width - 43) + "} {3:12}"
        inclusion_data = supersets.get_symbol_inclusion(symbol.ident)
        incl_projects = sorted(inclusion_data.keys(),
                               key=lambda x: inclusion_data[x][2])
        print(Style.BRIGHT + "Inclusion" + Style.NORMAL)
        if not len(inclusion_data):
            print("--- No known uses of this component ---")
        else:
            for project in incl_projects:
                ldata = inclusion_data[project]
                if not ldata[4]:
                    qtystr = str(ldata[3])
                else:
                    qtystr = '{0}-{1}'.format(ldata[3], ldata[4])
                if len(ldata[0]) > width-43:
                    pdesc = ldata[0][:width-46] + '...'
                else:
                    pdesc = ldata[0]
                pstatus = ldata[2].terminal_repr
                print(inclformat.format(project, qtystr, pdesc, pstatus))
    terminal.render_hline()


def main():
    """
    The tendril-gedaif script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    done = False
    verbose = args.verbose or args.pricing or args.utilization
    idents = gsymlib.gsymlib_idents
    if args.search:
        if args.regex:
            rex = re.compile(args.search)
            ridents = [ident for ident in idents if rex.search(ident)]
        else:
            ridents = [ident for ident in idents if args.search in ident]
        rsymbols = [gsymlib.get_symbol(ident) for ident in ridents]
        if len(rsymbols):
            terminal.render_hline()
        if args.pricing is True:
            pricing = args.quantity
        else:
            pricing = False
        for symbol in rsymbols:
            render_symbol(symbol, verbose, args.utilization, pricing)
        if not verbose:
            terminal.render_hline()
        done = True
    if not done:
        parser.print_help()


if __name__ == '__main__':
    main()
