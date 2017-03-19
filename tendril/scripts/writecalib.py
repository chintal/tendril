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
Device Calibration Writer Script (``tendril-writecalib``)
=========================================================

Writes calibration data to a device.

.. hint::

     - The calibration data is retrieved and calculated from the latest
       test results linked to the serial number of the device.
     - The commands to write to the device and the format of the calibration
       data are defined by the ``calibformat`` defined in the relevant
       product definition.

.. seealso::
    :func:`tendril.entityhub.products.get_product_calibformat`
    :func:`tendril.testing.testrunner.write_to_device`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.writecalib
    :func: _get_parser
    :prog: tendril-writecalib
    :nodefault:

"""


import argparse

from tendril.entityhub import macs
from tendril.entityhub import serialnos
from tendril.testing import testrunner
from .helpers import add_base_options

from tendril.utils import log
logger = log.get_logger("writecalib", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-writecalib script.
    """
    parser = argparse.ArgumentParser(
        description='Write calibration parameters to device.',
        prog='tendril-writecalib'
    )
    add_base_options(parser)
    parser.add_argument(
        'serialno', metavar='SNO', type=str, nargs='?',
        help='Device serial number'
    )
    parser.add_argument(
        '--detect', '-d', metavar=('MACTYPE'), type=str, nargs=1,
        help='Autodetect serial number using the specified MACTYPE. '
             'No effect if serial number specified.'
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true', default=False,
        help="Dry run only. Don't actually write to device."
    )
    return parser


def run(serialno=None):
    """
    Write calibration to device.

    :param serialno: The serial number of the device.

    """
    if serialno is None:
        raise AttributeError("serialno cannot be None")

    devicetype = serialnos.get_serialno_efield(sno=serialno)
    logger.info(serialno + " is device : " + devicetype)

    testrunner.write_to_device(serialno, devicetype)

    # user_input = raw_input("Print to Paper [y/N] ?: ").strip()
    # if user_input.lower() in ['y', 'yes', 'ok', 'pass']:
    #     testrunner.publish_and_print(
    #         serialno, devicetype, print_to_paper=True
    #     )
    # else:
    #     testrunner.publish_and_print(
    #         serialno, devicetype, print_to_paper=False
    #     )


def main():
    """
    The tendril-writecalib script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    if not args.serialno and not args.detect:
        parser.print_help()
        return
    if args.dry_run:
        print "Dry run not yet implemented. Not doing anything."
        return
    if not args.serialno:
        try:
            mactype = args.detect[0]
            sno = macs.get_sno_from_device(mactype)
        except:
            logger.error("Got exception when trying to detect serialno")
            raise
    else:
        sno = args.serialno
    run(sno)


if __name__ == '__main__':
    main()
