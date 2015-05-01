"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log

logger = log.get_logger(__name__, log.INFO)

import yaml
import csv
import os

import boms.electronics
import boms.outputbase

import inventory.electronics
import conventions.electronics
import sourcing.electronics

from entityhub import projects
from gedaif import projfile

from utils.progressbar.progressbar import ProgressBar
import inventory.guidelines

from utils.config import KOALA_ROOT


bomlist = []

orderfolder = os.path.join(KOALA_ROOT, 'scratch')
orderfile = os.path.join(orderfolder, 'order.yaml')

with open(orderfile, 'r') as f:
    data = yaml.load(f)

LOAD_PRESHORT = False
LOAD_EXTERNAL_REQ = False
external_req_file = None
USE_STOCK = True
IS_INDICATIVE = False
indication_context = None

if 'preshort' in data.keys():
    LOAD_PRESHORT = data['preshort']
if 'external' in data.keys():
    external_req_file = os.path.join(orderfolder, data['external'])
    LOAD_EXTERNAL_REQ = True
if 'use_stock' in data.keys():
    USE_STOCK = data['use_stock']
if 'is_indicative' in data.keys():
    IS_INDICATIVE = data['is_indicative']
    indication_context = data['context']


# Define base transforms for external data
base_tf = inventory.electronics.inventory_locations[0]._reader.tf

if LOAD_PRESHORT is True:
    # Load Preshort File
    if os.path.exists(os.path.join(orderfolder, 'preshort.csv')):
        with open(os.path.join(orderfolder, 'preshort.csv'), 'r') as f:
            logger.debug('Creating PRESHORT Bom')
            obom_descriptor = boms.outputbase.OutputElnBomDescriptor('PRESHORT', os.path.join(KOALA_ROOT, 'scratch'),
                                                                     'PRESHORT', None)
            obom = boms.outputbase.OutputBom(obom_descriptor)

            reader = csv.reader(f)
            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == 'S.No.':
                    continue
                if line[1] == line[2] == line[3]:
                    continue
                if line[1] == 'Electricals':
                    break
                if base_tf.has_contextual_repr(line[1]):
                    device, value, footprint = conventions.electronics.parse_ident(base_tf.get_canonical_repr(line[1]))
                    item = boms.electronics.EntityElnComp()
                    item.define('Undef', device, value, footprint)
                    for i in range(int(line[2]) + 1):
                        obom.insert_component(item)
                else:
                    print line[1], 'No'
            logger.info('Inserting PRESHORT Bom')
            bomlist.append(obom)

# Load External Requisitions
if LOAD_EXTERNAL_REQ is True:
    if os.path.exists(external_req_file):
        with open(external_req_file, 'r') as f:
            header = []
            reader = csv.reader(f)
            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == 'Device':
                    header = line
                    break

            logger.info('Inserting External Boms')
            oboms = []
            for head in header[1:]:
                logger.debug('Creating Bom : ' + head)
                obom_descriptor = boms.outputbase.OutputElnBomDescriptor(head, os.path.join(KOALA_ROOT, 'scratch'),
                                                                         head, None)
                obom = boms.outputbase.OutputBom(obom_descriptor)
                oboms.append(obom)

            for line in reader:
                line = [elem.strip() for elem in line]
                if line[0] == '':
                    continue
                if line[0] == 'END':
                    break
                if not base_tf.has_contextual_repr(line[0]):
                    print line[0] + ' Possibly not recognized'
                device, value, footprint = conventions.electronics.parse_ident(base_tf.get_canonical_repr(line[0]))
                # print base_tf.get_canonical_repr(line[0])
                item = boms.electronics.EntityElnComp()
                item.define('Undef', device, value, footprint)
                for idx, col in enumerate(line[1:]):
                    num = int(col)
                    if num > 0:
                        for i in range(num):
                            oboms[idx].insert_component(item)

            for obom in oboms:
                logger.info('Inserting External Bom : ' + obom.descriptor.configname)
                bomlist.append(obom)


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

with open(os.path.join(orderfolder, 'cobom.csv'), 'w') as f:
    logger.info('Exporting Composite Output BOM to File : ' + os.linesep + os.path.join(orderfolder, 'cobom.csv'))
    cobom.dump(f)



orders_path = os.path.join(orderfolder, 'purchase-orders')
if not os.path.exists(orders_path):
    os.makedirs(orders_path)

reservations_path = os.path.join(orderfolder, 'reservations')
if not os.path.exists(reservations_path):
    os.makedirs(reservations_path)

unsourced = []
pb = ProgressBar('red', block='#', empty='.')
nlines = len(cobom.lines)

for pbidx, line in enumerate(cobom.lines):
    percentage = (float(pbidx) / nlines) * 100.00
    pb.render(int(percentage),
              "\n{0:>7.4f}% {1:<40} Qty:{2:<4}\nConstructing Shortage File, Reservations, and Preparing Orders".format(
                  percentage, line.ident, line.quantity))
    shortage = 0
    if USE_STOCK is True:
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
    else:
        shortage = line.quantity
    if shortage > 0:
        result = sourcing.electronics.order.add(line.ident, line.quantity, shortage)
        if result is False:
            unsourced.append((line.ident, shortage))

if len(unsourced) > 0:
    logger.warning("Unable to source the following components: ")
    for elem in unsourced:
        logger.warning("{0:<40}{1:>5}".format(elem[0], elem[1]))
sourcing.electronics.order.collapse()
sourcing.electronics.order.rebalance()
sourcing.electronics.order.generate_orders(orders_path)
sourcing.electronics.order.dump_to_file(os.path.join(orderfolder, 'shortage.csv'), include_others=True)
inventory.electronics.export_reservations(reservations_path)

if IS_INDICATIVE:
    logger.info('Generating Indicative Pricing Files')
    logger.debug('Loading Ident Pricing Information')
    pricing = {}
    if USE_STOCK:
        logger.warning("Possibly Incorrect Analysis : Using Stock for Indicative Pricing Calculation")
    with open(os.path.join(orderfolder, 'shortage.csv'), 'r') as f:
        reader = csv.reader(f)
        headers = None
        for row in reader:
            if row[0] == 'Ident':
                headers = row
                break
        for row in reader:
            if row[0] is not '':
                if row[0] not in pricing.keys():
                    try:
                        pricing[row[0]] = (row[headers.index('Vendor')],
                                           row[headers.index('Vendor Part No')],
                                           row[headers.index('Manufacturer')],
                                           row[headers.index('Manufacturer Part No')],
                                           row[headers.index('Description')],
                                           row[headers.index('Used Break Qty')],
                                           row[headers.index('Effective Unit Price')]
                                           )
                    except IndexError:
                        pricing[row[0]] = None
    summaryf = open(os.path.join(orderfolder, 'costing-summary.csv'), 'w')
    summaryw = csv.writer(summaryf)
    summaryw.writerow(["Card", "Total BOM Lines", "Uncosted BOM Lines", "Quantity",
                       "Indicative Unit Cost", "Indicative Line Cost"
                       ])
    all_uncosted_idents = []
    for k, v in sorted(data['cards'].iteritems()):
        logger.info('Creating Indicative Pricing for Card : ' + k)
        bom = boms.electronics.import_pcb(projects.cards[k])
        obom = bom.create_output_bom(k)
        gpf = projfile.GedaProjectFile(obom.descriptor.cardfolder)
        ipfolder = gpf.configsfile.indicative_pricing_folder
        if not os.path.exists(ipfolder):
            os.makedirs(ipfolder)
        ipfile = os.path.join(ipfolder, obom.descriptor.configname + '~' + indication_context + '.csv')
        totalcost = 0
        uncosted_idents = []
        total_lines = 0
        with open(ipfile, 'w') as f:
            writer = csv.writer(f)
            headers = ['Ident',
                       'Vendor', 'Vendor Part No',
                       'Manufacturer', 'Manufacturer Part No', 'Description',
                       'Used Break Qty', 'Effective Unit Price',
                       'Quantity', 'Line Price']
            writer.writerow(headers)
            for line in obom.lines:
                total_lines += 1
                if pricing[line.ident][0].strip() != '':
                    try:
                        writer.writerow([line.ident] + list(pricing[line.ident]) +
                                        [line.quantity, line.quantity * float(pricing[line.ident][-1])])
                    except ValueError:
                        print pricing[line.ident][-1]
                        raise ValueError
                    totalcost += line.quantity * float(pricing[line.ident][-1])
                else:
                    writer.writerow([line.ident] + [None] * (len(headers) - 3) + [line.quantity] + [None])
                    uncosted_idents.append([line.ident])

            summaryw.writerow([k, total_lines, len(uncosted_idents), v, totalcost, totalcost * v])
            logger.info('Indicative Pricing for Card ' + k + ' Written to File : ' + os.linesep + ipfile)
            for ident in uncosted_idents:
                if ident not in all_uncosted_idents:
                    all_uncosted_idents.append(ident)
    summaryw.writerow([])
    summaryw.writerow([])
    summaryw.writerow(["Uncosted Idents : "])
    for ident in sorted(all_uncosted_idents):
        summaryw.writerow(ident)
    summaryf.close()
    logger.info(
        'Indicative Pricing Summary Written to File : ' + os.linesep + os.path.join(orderfolder, 'costing-summary.csv'))

