"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


import boms.electronics
import render
import os


def gen_assemmanifest(projfolder, configname, outpath=None, sno=None):
    if sno is None:
        # TODO Generate real S.No. here
        sno = 1
    else:
        # TODO Verify S.no. is correct and create if needed
        pass

    if outpath is None:
        # TODO Generate correct outpath here
        outpath = os.path.normpath(projfolder + '/am-' + configname + '-' + str(sno) + '.pdf')

    bom = boms.electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    stage = {'configname': obom.descriptor.configname,
             'sno': sno,
             'lines': obom.lines}

    template = 'pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)

