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

import os
import argparse

from tendril.inventory.electronics import get_total_availability
from tendril.inventory.electronics import reserve_items

from tendril.utils.terminal import TendrilProgressBar
from tendril.utils.config import INSTANCE_ROOT

from tendril.production.order import ProductionOrder

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


def get_line_shortage(line, descriptors):
    shortage = 0
    logger.debug("Processing Line : " + line.ident)
    for idx, descriptor in enumerate(descriptors):
        logger.debug("    for earmark : " + descriptor.configname)
        earmark = descriptor.configname + \
            ' x' + str(descriptor.multiplier)
        avail = get_total_availability(line.ident)  # noqa
        if line.columns[idx] == 0:
            continue
        if avail > line.columns[idx]:
            reserve_items(line.ident, line.columns[idx], earmark)
        elif avail > 0:
            reserve_items(line.ident, avail, earmark)
            pshort = line.columns[idx] - avail
            shortage += pshort
            logger.debug('Adding Partial Qty of ' + line.ident +
                         ' for ' + earmark + ' to shortage ' +
                         str(pshort))
        else:
            shortage += line.columns[idx]
            logger.debug('Adding Full Qty of ' + line.ident +
                         ' for ' + earmark + ' to shortage : ' +
                         str(line.columns[idx]))
    return shortage


def generate_indent(bomlist, orderfolder, data, prod_ord_sno,
                    indentsno=None, register=False, verbose=False,
                    halt_on_shortage=False):
    unsourced = []
    nlines = len(cobom.lines)
    pb = TendrilProgressBar(max=nlines)

    for pbidx, line in enumerate(cobom.lines):
        pb.next(note=line.ident)
        shortage = get_line_shortage(line, cobom.descriptors)
        if shortage > 0:
            unsourced.append((line.ident, shortage))

    if len(unsourced) > 0:
        print("Shortage of the following components: ")
        for elem in unsourced:
            print("{0:<40}{1:>5}".format(elem[0], elem[1]))
        if halt_on_shortage is True:
            print ("Halt on shortage is set. Reversing changes "
                   "and exiting")
            exit()

    # TODO Transfer Reservations


def main(orderfolder=None, orderfile_r=None,
         register=None, verbose=True):

    if orderfile_r is None:
        orderfile_r = 'order.yaml'
    if orderfolder is None:
        orderfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production')

    orderfile = os.path.join(orderfolder, orderfile_r)

    if os.path.exists(os.path.join(orderfolder, 'wsno')):
        with open(os.path.join(orderfolder, 'wsno'), 'r') as f:
            PROD_ORD_SNO = f.readline().strip()
    else:
        PROD_ORD_SNO = None

    snomap_path = None
    if os.path.exists(os.path.join(orderfolder, 'snomap.yaml')):
        snomap_path = os.path.join(orderfolder, 'snomap.yaml')

    production_order = ProductionOrder(sno=PROD_ORD_SNO)
    production_order.create(order_yaml_path=orderfile,
                            snomap_path=snomap_path)

    if register is None:
        REGISTER = False
    else:
        REGISTER = register

    production_order.process(outfolder=orderfile, manifestsfolder=None,
                             register=REGISTER, session=None)


def entry_point():
    parser = argparse.ArgumentParser(
        description='Generate production orders and associated documentation.',
        prog='tendril-production'
    )
    parser.add_argument(
        '--order-folder', '-d', metavar='PATH', type=str, nargs='?',
        help='Path to the order folder. Search location for order files and '
             'write location for output files. Defaults to '
             'INSTANCE_FOLDER/scratch/production.'
    )
    parser.add_argument(
        '--order-file', metavar='PATH', type=str, nargs='?',
        help='Relative path to the order file (yaml) from the order-folder. '
             'Defaults to order.yaml'
    )
    parser.add_argument(
        '--execute', '-e', action='store_true', default=False,
        help="Register on the database, publish any/all files. "
             "The setting here will override anything in the order file."
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', default=None,
        help="Increase output verbosity."
    )

    args = parser.parse_args()
    main(orderfolder=args.order_folder,
         orderfile_r=args.order_file,
         register=args.execute,
         verbose=args.verbose)

if __name__ == '__main__':
    main()
