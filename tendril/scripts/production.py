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
Generate Production Order Script (``tendril-production``)
=========================================================

This script generates a production order from a provided
``order.yaml`` file.

.. hint::
    By default, this script does not register any of its
    actions. Call the script with the execute flag in order to
    commit the results to the database.

.. hint::
    The default order folder this script uses / looks in is in the
    production workspace of the tendril instance, typically
    ``$HOME/.tendril/scratch/production``.

.. warning::

    The script relies on the following files to manage serial numbers
    when it is run multiple times :

        - ``ORDERFOLDER/snomap.yaml``
        - ``ORDERFOLDER/wsno``

    When the first simulated run is executed, the ``snomap.yaml`` file is
    created with dummy serial numbers. In order to then generate and
    register a real production order, you should delete the ``snomap.yaml``
    file.

    The ``wsno`` file is created when an old production order is retrived
    using ``tendril-getdox``. This file makes sure if the production order
    is regenerated, it uses the same production order serial number.

     - When operating on retrieved, old production orders, make sure to not
       remove the ``wsno`` file.
     - When operating on a new production order, make sure to remove any
       stale ``wsno`` files that may be in the workspace from a past run.

.. hint::
    It'll probably be easier to simply wipe the entire production order
    folder clean when starting work on a new production order. You can
    retain the ``order.yaml`` file to use as a template for the new order,
    and get rid of everything else.

.. seealso::
    :mod:`tendril.production.order`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.production
    :func: _get_parser
    :prog: tendril-production
    :nodefault:

"""

import os
import argparse

from tendril.dox.labelmaker import get_manager
from tendril.utils.config import INSTANCE_ROOT

from tendril.production.order import ProductionOrder
from .helpers import add_base_options

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-production script.
    """
    parser = argparse.ArgumentParser(
        description='Generate production orders and associated documentation.',
        prog='tendril-production'
    )
    add_base_options(parser)
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
        '--force', '-f', action='store_true', default=None,
        help="Force execution. Currently applies to Deltas, bypassing "
             "DeltaValidationErrors."
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true', default=None,
        help="Increase output verbosity."
    )
    return parser


def main(orderfolder=None, orderfile_r=None,
         register=None, verbose=True, force=False):
    """
    Production order generation function.
    """
    if orderfile_r is None:
        orderfile_r = 'order.yaml'
    if orderfolder is None:
        orderfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production')

    orderfile = os.path.join(orderfolder, orderfile_r)

    if os.path.exists(os.path.join(orderfolder, 'wsno')):
        with open(os.path.join(orderfolder, 'wsno'), 'r') as f:
            prod_ord_sno = f.readline().strip()
    else:
        prod_ord_sno = None

    snomap_path = None
    if os.path.exists(os.path.join(orderfolder, 'snomap.yaml')):
        snomap_path = os.path.join(orderfolder, 'snomap.yaml')

    labelmanager = get_manager()

    production_order = ProductionOrder(sno=prod_ord_sno)
    production_order.create(order_yaml_path=orderfile,
                            snomap_path=snomap_path,
                            force=force)

    if register is None:
        register = False

    production_order.process(outfolder=orderfolder, manifestsfolder=None,
                             label_manager=labelmanager, register=register,
                             force=force, session=None)

    labelmanager.generate_pdfs(orderfolder, force=True)


def entry_point():
    """
    The tendril-production script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    main(orderfolder=args.order_folder,
         orderfile_r=args.order_file,
         register=args.execute,
         verbose=args.verbose,
         force=args.force)


if __name__ == '__main__':
    entry_point()
