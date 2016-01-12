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
import yaml
import argparse

from tendril.boms.electronics import import_pcb
from tendril.boms.outputbase import CompositeOutputBom

from tendril.inventory.electronics import get_total_availability
from tendril.inventory.electronics import reserve_items

from tendril.dox.production import gen_production_order
from tendril.dox.production import gen_pcb_am
from tendril.dox.production import gen_delta_pcb_am
from tendril.dox.production import get_production_strategy

from tendril.dox.indent import gen_stock_idt_from_cobom
from tendril.dox import docstore
from tendril.dox import labelmaker

from tendril.entityhub import projects
from tendril.entityhub import serialnos

from tendril.utils.pdf import merge_pdf
from tendril.utils.terminal import TendrilProgressBar
from tendril.utils.config import INSTANCE_ROOT

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


def main(orderfolder=None, orderfile_r=None,
         register=None, verbose=True):
    bomlist = []
    if orderfile_r is None:
        orderfile_r = 'order.yaml'
    if orderfolder is None:
        orderfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production')

    orderfile = os.path.join(orderfolder, orderfile_r)

    with open(orderfile, 'r') as f:
        data = yaml.load(f)

    if os.path.exists(os.path.join(orderfolder, 'wsno')):
        with open(os.path.join(orderfolder, 'wsno'), 'r') as f:
            PROD_ORD_SNO = f.readline().strip()
    else:
        PROD_ORD_SNO = None

    snomap = {}
    if os.path.exists(os.path.join(orderfolder, 'snomap.yaml')):
        with open(os.path.join(orderfolder, 'snomap.yaml'), 'r') as f:
            snomap = yaml.load(f)

    if register is None:
        if 'register' in data.keys():
            if data['register'] is True:
                REGISTER = True
            else:
                REGISTER = False
        else:
            REGISTER = False
    else:
        REGISTER = register

    if data['halt_on_shortage'] is True:
        HALT_ON_SHORTAGE = True
    else:
        HALT_ON_SHORTAGE = False

    if data['force_labels'] is True:
        FORCE_LABELS = True
    else:
        FORCE_LABELS = False

    if 'sourcing_orders' in data.keys():
        SOURCING_ORDERS = data['sourcing_orders']
    else:
        SOURCING_ORDERS = None

    if 'root_orders' in data.keys():
        ROOT_ORDERS = data['root_orders']
        if len(ROOT_ORDERS) > 1:
            logger.warning("Having more than one Root Order is not fully "
                           "defined. This may break other functionality")
    else:
        ROOT_ORDERS = None

    if PROD_ORD_SNO is None:
        PROD_ORD_SNO = serialnos.get_serialno(series='PROD',
                                              efield=data['title'],
                                              register=REGISTER)

    manifestsfolder = os.path.join(orderfolder, 'manifests')
    if not os.path.exists(manifestsfolder):
        os.makedirs(manifestsfolder)
    manifestfiles = []
    addldocs = []
    snos = []

    # Generate Tendril Requisitions, confirm production viability.
    if 'cards' in data.keys():
        if verbose:
            print('Generating Card BOMs')
        for k, v in data['cards'].iteritems():
            bom = import_pcb(projects.cards[k])
            obom = bom.create_output_bom(k)
            obom.multiply(v)
            print('Inserting Card Bom : {0} x{1}'.format(
                obom.descriptor.configname, obom.descriptor.multiplier
            ))
            bomlist.append(obom)
    if 'deltas' in data.keys():
        if verbose:
            print('Generating Delta BOMs and Manifests')
        for delta in data['deltas']:
            dmpath, delta_obom = gen_delta_pcb_am(
                delta['orig-cardname'], delta['target-cardname'],
                outfolder=manifestsfolder, sno=delta['sno']
            )
            obom = delta_obom.additions_bom
            print('Inserting Delta Addition Bom : {0}'.format(
                obom.descriptor.configname
            ))
            bomlist.append(obom)
            manifestfiles.append(dmpath)
            if REGISTER is True:
                docstore.register_document(serialno=delta['sno'], docpath=dmpath,
                                           doctype='DELTA ASSEMBLY MANIFEST')

            strategy = get_production_strategy(delta['target-cardname'])
            prodst, lblst, testst, genmanifest, genlabel, series, labels = strategy  # noqa
            desc = delta['orig-cardname'] + ' -> ' + delta['target-cardname']
            c = {'sno': delta['sno'], 'ident': delta['target-cardname'],
                 'prodst': '@AM', 'lblst': lblst, 'testst': testst,
                 'is_delta': True, 'desc': desc
                 }
            snos.append(c)
            if genlabel is True:
                for label in labels:
                    labelmaker.manager.add_label(
                        label['code'], label['ident'], delta['sno']
                    )

    if len(bomlist) == 0:
        indentsno = None
    else:
        cobom = CompositeOutputBom(bomlist)
        cobom.collapse_wires()

        with open(os.path.join(orderfolder, 'cobom.csv'), 'w') as f:
            if verbose:
                print('Exporting Composite Output BOM to File : ' + os.linesep +
                      os.path.join(orderfolder, 'cobom.csv'))
            cobom.dump(f)

        unsourced = []
        nlines = len(cobom.lines)
        pb = TendrilProgressBar(max=nlines)

        for pbidx, line in enumerate(cobom.lines):
            pb.next(note=line.ident)
            shortage = 0
            logger.debug("Processing Line : " + line.ident)
            for idx, descriptor in enumerate(cobom.descriptors):
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

            if shortage > 0:
                unsourced.append((line.ident, shortage))

        if len(unsourced) > 0:
            print("Shortage of the following components: ")
            for elem in unsourced:
                print("{0:<40}{1:>5}".format(elem[0], elem[1]))
            if HALT_ON_SHORTAGE is True:
                print ("Halt on shortage is set. Reversing changes "
                       "and exiting")
                exit()

        # TODO Transfer Reservations
        # Generate Indent
        if verbose:
            print("Generating Indent")

        indentfolder = orderfolder
        if 'indentsno' in snomap.keys():
            indentsno = snomap['indentsno']
        else:
            indentsno = serialnos.get_serialno(series='IDT',
                                               efield='FOR ' + PROD_ORD_SNO,
                                               register=REGISTER)
            snomap['indentsno'] = indentsno
        title = data['title']
        indent_context = {}
        if 'cards' in data.keys():
            indent_context.update(data['cards'])
        if 'deltas' in data.keys():
            for delta in data['deltas']:
                desc = delta['orig-cardname'] + ' -> ' + delta['target-cardname']
                if desc in indent_context.keys():
                    indent_context[desc] += 1
                else:
                    indent_context[desc] = 1
        indentpath, indentsno = gen_stock_idt_from_cobom(
                indentfolder, indentsno, title, indent_context, cobom
        )
        if REGISTER is True:
            docstore.register_document(serialno=indentsno,
                                       docpath=indentpath,
                                       doctype='INVENTORY INDENT',
                                       efield=title)
        else:
            print(
                "Not Registering Document : INVENTORY INDENT - " + indentsno
            )

    # Generate Production Order
    if verbose:
        print("Generating Production Order")
    if indentsno is not None:
        if REGISTER is True:
            docstore.register_document(serialno=indentsno,
                                       docpath=os.path.join(orderfolder, 'cobom.csv'),  # noqa
                                       doctype='PRODUCTION COBOM CSV',
                                       efield=title)
            serialnos.link_serialno(child=indentsno, parent=PROD_ORD_SNO)
        else:
            print("Not registering used serial number : " +
                  PROD_ORD_SNO)
            print("Not Registering Document : PRODUCTION COBOM CSV - " +
                  indentsno)
            print("Not Linking Serial Nos : " + indentsno +
                  ' to parent ' + PROD_ORD_SNO)

    if 'cards' in data.keys():
        for card, qty in sorted(data['cards'].iteritems()):
            cardfolder = projects.cards[card]
            strategy = get_production_strategy(card)
            prodst, lblst, testst, genmanifest, genlabel, series, labels = strategy  # noqa
            for idx in range(qty):
                if card in snomap.keys():
                    if idx in snomap[card].keys():
                        sno = snomap[card][idx]
                    else:
                        sno = serialnos.get_serialno(
                            series=series, efield=card, register=REGISTER
                        )
                        snomap[card][idx] = sno
                else:
                    snomap[card] = {}
                    sno = serialnos.get_serialno(
                        series=series, efield=card, register=REGISTER
                    )
                    snomap[card][idx] = sno
                if REGISTER is True:
                    serialnos.link_serialno(child=sno, parent=PROD_ORD_SNO)
                c = {'sno': sno, 'ident': card,
                     'prodst': prodst, 'lblst': lblst, 'testst': testst,
                     'is_delta': False
                     }
                snos.append(c)
                if genlabel is True:
                    for label in labels:
                        labelmaker.manager.add_label(
                            label['code'], label['ident'], sno
                        )
                if genmanifest is True:
                    ampath = gen_pcb_am(cardfolder, card,
                                        manifestsfolder, sno,
                                        productionorderno=PROD_ORD_SNO,
                                        indentsno=indentsno)
                    manifestfiles.append(ampath)
                    if REGISTER is True:
                        docstore.register_document(serialno=sno, docpath=ampath,  # noqa
                                                   doctype='ASSEMBLY MANIFEST')  # noqa

    production_order = gen_production_order(orderfolder, PROD_ORD_SNO,
                                            data, snos,
                                            sourcing_orders=SOURCING_ORDERS,
                                            root_orders=ROOT_ORDERS)
    labelpaths = labelmaker.manager.generate_pdfs(orderfolder,
                                                  force=FORCE_LABELS)

    if len(labelpaths) > 0:
        merge_pdf(
            labelpaths,
            os.path.join(orderfolder, 'device-labels.pdf')
        )
    if len(addldocs) > 0:
        merge_pdf(
            [production_order] + addldocs,
            production_order,
            remove_sources=False
        )
    if len(manifestfiles) > 0:
        merge_pdf(
            manifestfiles,
            os.path.join(orderfolder, 'manifests-printable.pdf')
        )

    if REGISTER is True:
        if os.path.exists(os.path.join(orderfolder, 'device-labels.pdf')):
            docstore.register_document(serialno=PROD_ORD_SNO,
                                       docpath=os.path.join(orderfolder, 'device-labels.pdf'),  # noqa
                                       doctype='DEVICE LABELS',
                                       efield=data['title'])
        docstore.register_document(serialno=PROD_ORD_SNO,
                                   docpath=production_order,
                                   doctype='PRODUCTION ORDER',
                                   efield=data['title'])
        docstore.register_document(serialno=PROD_ORD_SNO,
                                   docpath=orderfile,
                                   doctype='PRODUCTION ORDER YAML',  # noqa
                                   efield=data['title'])
    else:
        print(
            "Not registering document : DEVICE LABELS " + PROD_ORD_SNO
        )
        print(
            "Not registering document : PRODUCTION ORDER " + PROD_ORD_SNO
        )
        print(
            "Not registering document : PRODUCTION ORDER YAML " + PROD_ORD_SNO
        )

    with open(os.path.join(orderfolder, 'snomap.yaml'), 'w') as f:
        f.write(yaml.dump(snomap, default_flow_style=False))
    if REGISTER is True:
        docstore.register_document(serialno=PROD_ORD_SNO,
                                   docpath=os.path.join(orderfolder, 'snomap.yaml'),  # noqa
                                   doctype='SNO MAP',
                                   efield=data['title'])


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
