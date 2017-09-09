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
import csv
import argparse

from tendril.gedaif import gsymlib
from tendril.entityhub import supersets
from tendril.conventions.status import print_status
from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import MalformedIdentError

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
        help='Ident search string.'
    )
    parser.add_argument(
        '--device', metavar='DEVICE', type=str,
        help='Filter by Device'
    )
    parser.add_argument(
        '--footprint', metavar='FOOTPRINT', type=str,
        help='Filter by Footprint'
    )
    parser.add_argument(
        '--manufacturer', metavar='MANUFACTURER', type=str,
        help='Filter by Manufacturer'
    )
    parser.add_argument(
        '--vendor', metavar='VENDOR', type=str,
        help='Filter by Vendor'
    )
    parser.add_argument(
        '-z', '--used', action='store_true', default=False,
        help='Show only symbols with known uses.'
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
        help='Print symbol pricing information. Provides pricing for '
             'the lowest guideline compliant quantity unless otherwise '
             'specified using -q.'
    )
    parser.add_argument(
        '-q', '--quantity', action='store', default=1, type=int,
        help='Retrieve information for a different quantity.'
    )
    parser.add_argument(
        '--csv', action='store', metavar='FILENAME', default=None,
        help='Generate CSV output instead of human readable '
             'terminal text. Prov'
    )
    return parser


def render_symbol(symbol, verbose=False, inclusion=False, pricing=False):
    width = terminal.get_terminal_width()
    symformat = "{0:<" + str(width - 13) + "} {1:>2}"
    if inclusion or pricing:
        verbose = True
    if not verbose:
        print(symformat.format(symbol.ident,
                               print_status(symbol.status)))
        return
    title = symformat.format(symbol.ident,
                             print_status(symbol.status))
    print(Style.BRIGHT + title + Style.NORMAL)
    detailformat = "{0:<15} {1}"
    print(detailformat.format('Description', symbol.description))
    if symbol.datasheet_url:
        print(detailformat.format('Datasheet', symbol.datasheet_url))
    if symbol.manufacturer:
        print(detailformat.format('Manufacturer', symbol.manufacturer))
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
            isiformat = "{0:27} {1:37} {2:6} (@{3})"
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
                pstatus = print_status(ldata[2])
                print(inclformat.format(project, qtystr, pdesc, pstatus))
    terminal.render_hline()


def output_symbol(writer, symbol, inclusion=False, pricing=False):
    writer.writerow([symbol.ident])
    if pricing:
        raise NotImplementedError("Pricing output to CSV not yet implemented")
    if inclusion:
        inclusion_data = supersets.get_symbol_inclusion(symbol.ident)
        incl_projects = sorted(inclusion_data.keys(),
                               key=lambda x: inclusion_data[x][2])
        if not len(inclusion_data):
            return
        else:
            for project in incl_projects:
                ldata = inclusion_data[project]
                if not ldata[4]:
                    qtystr = str(ldata[3])
                else:
                    qtystr = '{0}-{1}'.format(ldata[3], ldata[4])
                pdesc = ldata[0]
                pstatus = ldata[2]
                writer.writerow(['', qtystr, project, pstatus])


def prefilter_idents(idents, args):
    if not args.device and not args.footprint \
            and not args.search and not args.used:
        for ident in idents:
            yield ident
    dcmp = fcmp = scmp = None
    d = f = None
    if args.regex:
        if args.device:
            dregex = re.compile(args.device)
            dcmp = lambda x: dregex.search(x)
        if args.footprint:
            fregex = re.compile(args.footprint)
            fcmp = lambda x: fregex.search(x)
        if args.search:
            sregex = re.compile(args.search)
            scmp = lambda x: sregex.search(x)
    else:
        if args.device:
            dcmp = lambda x: args.device in x
        if args.footprint:
            fcmp = lambda x: args.footprint in x
        if args.search:
            scmp = lambda x: args.search in x

    for i in idents:
        if dcmp or fcmp:
            try:
                d, v, f = parse_ident(i)
            except MalformedIdentError:
                continue
        if dcmp:
            if not d or not dcmp(d):
                continue
        if fcmp:
            if not f or not fcmp(f):
                continue
        if scmp and not scmp(i):
            continue
        if args.used:
            if not len(supersets.get_symbol_inclusion(i).keys()):
                continue
        yield i


def get_and_postfilter_symbols(idents, args):
    mcmp = vcmp = None
    if args.regex:
        if args.manufacturer:
            mregex = re.compile(args.manufacturer)
            mcmp = lambda x: mregex.search(x)
        if args.vendor:
            vregex = re.compile(args.vendor)
            vcmp = lambda x: vregex.search(x)
    else:
        if args.manufacturer:
            mcmp = lambda x: args.manufacturer in x
        if args.vendor:
            vcmp = lambda x: args.vendor in x
    for i in idents:
        try:
            s = gsymlib.get_symbol(i)
        except gsymlib.NoGedaSymbolException:
            continue
        if mcmp:
            if not s.manufacturer or not mcmp(s.manufacturer):
                continue
        if vcmp:
            if not s.vendors:
                continue
            found = False
            for v in s.vendors:
                if vcmp(v):
                    found = True
                    break
            if not found:
                continue
        yield s


def main():
    """
    The tendril-gedaif script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()

    verbose = args.verbose or args.pricing or args.utilization
    idents = sorted(gsymlib.gsymlib_idents)
    if args.pricing is True:
        pricing = args.quantity
    else:
        pricing = False

    idents = prefilter_idents(idents, args)

    # TODO Consider replacing this with branching partial functions instead
    if not args.csv:
        for symbol in get_and_postfilter_symbols(idents, args):
            render_symbol(symbol, verbose, args.utilization, pricing)
        if not verbose:
            terminal.render_hline()
    else:
        if args.utilization and pricing:
            print("Including both pricing and inclusion is not supported "
                  "in the CSV output")
        with open(args.csv, 'wb') as csvfile:
            writer = csv.writer(csvfile)
            for symbol in get_and_postfilter_symbols(idents, args):
                output_symbol(writer, symbol, args.utilization, pricing)


if __name__ == '__main__':
    main()
