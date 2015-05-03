"""
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""


import boms.electronics
import render
import os
from utils.pdf import merge_pdf


def gen_pcb_am(projfolder, configname, outfolder, sno=None):
    if sno is None:
        # TODO Generate real S.No. here
        sno = 1
    else:
        # TODO Verify S.no. is correct and create if needed
        pass

    outpath = os.path.join(outfolder,  'am-' + configname + '-' + str(sno) + '.pdf')

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
             'evenpages': evenpages}

    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)

    if add_schematic is True:
        merge_pdf([outpath, os.path.join(projfolder, 'doc', entityname + '-schematic.pdf')], outpath)

    return outpath

