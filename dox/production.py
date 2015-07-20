"""
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""


import os


import boms.electronics
import entityhub.projects
import entityhub.serialnos
from gedaif.conffile import ConfigsFile
from utils.pdf import merge_pdf

import render


def gen_pcb_am(projfolder, configname, outfolder, sno=None, productionorderno=None, indentsno=None, register=False):
    if sno is None:
        # TODO Generate real S.No. here
        sno = 1

    outpath = os.path.join(outfolder, 'am-' + configname + '-' + str(sno) + '.pdf')

    bom = boms.electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    if bom.configurations.rawconfig['pcbname'] is not None:
        entityname = bom.configurations.rawconfig['pcbname']
        title = 'PCB '
        evenpages = True
        add_schematic = False
    elif bom.configurations.rawconfig['cblname'] is not None:
        entityname = bom.configurations.rawconfig['cblname']
        title = 'Cable '
        evenpages = False
        add_schematic = True
    else:
        raise ValueError

    stage = {'configname': obom.descriptor.configname,
             'pcbname': entityname,
             'title': title,
             'sno': sno,
             'lines': obom.lines,
             'evenpages': evenpages,
             'stockindent': indentsno,
             'repopath': entityhub.projects.card_reporoot[obom.descriptor.configname],
             'productionorderno': productionorderno}

    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)

    if add_schematic is True:
        merge_pdf([outpath, os.path.join(projfolder, 'doc', entityname + '-schematic.pdf')], outpath)

    return outpath


def gen_production_order(outfolder, prod_sno, sourcedata, snos, sourcing_orders=None, root_orders=None):
    cards = [{'qty': sourcedata['cards'][k],
              'desc': ConfigsFile(entityhub.projects.cards[k]).description(k),
              'ident': k} for k in sorted(sourcedata['cards'].keys())]

    lroot_orders = []
    for root_order in root_orders:
        if root_order is not None:
            try:
                root_order_desc = entityhub.serialnos.get_sno_efield(root_order)
            except AttributeError:
                root_order_desc = None
        else:
            root_order_desc = None
        lroot_orders.append({'no': root_order, 'desc': root_order_desc})

    stage = {
        'title': sourcedata['title'],
        'cards': cards,
        'sourcing_orders': sourcing_orders,
        'sno': prod_sno,
        'snos': snos,
        'root_orders': lroot_orders,
    }

    outpath = os.path.join(outfolder, str(prod_sno) + '.pdf')
    template = 'production-order-template.tex'
    render.render_pdf(stage, template, outpath)
    return outpath
