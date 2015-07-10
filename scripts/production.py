"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log

logger = log.get_logger(__name__, log.INFO)

import yaml
import os

import boms.electronics
import boms.outputbase

import inventory.electronics
import dox.production
import dox.indent

from entityhub import projects
from entityhub import serialnos

from utils.pdf import merge_pdf
from utils.progressbar.progressbar import ProgressBar
from utils.config import INSTANCE_ROOT

bomlist = []

orderfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production', 'current')
orderfile = os.path.join(orderfolder, 'order.yaml')


with open(orderfile, 'r') as f:
    data = yaml.load(f)

# Generate Koala Requisitions
logger.info('Generating Card BOMs')
for k, v in data['cards'].iteritems():
    bom = boms.electronics.import_pcb(projects.cards[k])
    obom = bom.create_output_bom(k)
    obom.multiply(v)
    logger.info('Inserting Card Bom : ' + obom.descriptor.configname +
                ' x' + str(obom.descriptor.multiplier))
    bomlist.append(obom)

cobom = boms.outputbase.CompositeOutputBom(bomlist)
cobom.collapse_wires()

with open(os.path.join(orderfolder, 'cobom.csv'), 'w') as f:
    logger.info('Exporting Composite Output BOM to File : ' + os.linesep + os.path.join(orderfolder, 'cobom.csv'))
    cobom.dump(f)

unsourced = []
pb = ProgressBar('red', block='#', empty='.')
nlines = len(cobom.lines)

for pbidx, line in enumerate(cobom.lines):
    percentage = (float(pbidx) / nlines) * 100.00
    pb.render(int(percentage),
              "\n{0:>7.4f}% {1:<40} Qty:{2:<4}\nConstructing Reservations".format(
                  percentage, line.ident, line.quantity))
    shortage = 0

    for idx, descriptor in enumerate(cobom.descriptors):
        earmark = descriptor.configname + ' x' + str(descriptor.multiplier)
        avail = inventory.electronics.get_total_availability(line.ident)
        if line.columns[idx] == 0:
            continue
        if avail > line.columns[idx]:
            inventory.electronics.reserve_items(line.ident, line.columns[idx], earmark)
        elif avail > 0:
            inventory.electronics.reserve_items(line.ident, avail, earmark)
            pshort = line.columns[idx] - avail
            shortage += pshort
            logger.debug('Adding Partial Qty of ' + line.ident +
                         ' for ' + earmark + ' to shortage : ' + str(pshort))
        else:
            shortage += line.columns[idx]
            logger.debug('Adding Full Qty of ' + line.ident +
                         ' for ' + earmark + ' to shortage : ' + str(line.columns[idx]))

    if shortage > 0:
        unsourced.append((line.ident, shortage))

if len(unsourced) > 0:
    logger.warning("Shortage of the following components: ")
    for elem in unsourced:
        logger.warning("{0:<40}{1:>5}".format(elem[0], elem[1]))

logger.info("Generating Indent")

indentfolder = orderfolder
indentsno = data['sno']
title = data['title']
indentpath, indentsno = dox.indent.gen_stock_idt_from_cobom(orderfolder, indentsno, title, data['cards'], cobom)

logger.info("Generating Production Assembly Manifest")

manifestsfolder = os.path.join(orderfolder, 'manifests')
if not os.path.exists(manifestsfolder):
    os.makedirs(manifestsfolder)
manifestfiles = []

for card, qty in sorted(data['cards'].iteritems()):
    try:
        cardfolder = projects.cards[card]
    except KeyError:
        logger.error("Could not find Card in entityhub.cards")
        raise KeyError
    for idx in range(qty):
        # TODO Correct Series?
        series = 'QDA'
        # Use PCB/Card Serial Number instead
        cardsno = serialnos.get_serialno("QDA", efield=card, register=False)
        # TODO Figure out cables vs PCBs?
        # TODO Register Generated Documentation as well
        am_path = dox.production.gen_pcb_am(cardfolder, card,
                                            manifestsfolder,
                                            cardsno,
                                            indentsno)
        manifestfiles.append(am_path)
        logger.info("Trying to Register : " + cardsno + " : " + am_path)
        # serialnos.register_document(cardsno, am_path, "ASSEMBLY MANIFEST", card)


merge_pdf(manifestfiles, os.path.join(orderfolder, 'manifests.pdf'))
