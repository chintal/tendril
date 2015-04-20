"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
import subprocess
import utils.pdf


def conv_pcb2pdf(pcbpath, docfolder, projname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    psfile = os.path.join(docfolder, projname+'-pcb.ps')
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--outline', '--media', 'A4', '--show-legend',
                     pcb_file], cwd=pcb_folder)
    pdffile = os.path.join(docfolder, projname+'-pcb.pdf')
    utils.pdf.conv_ps2pdf(psfile, pdffile)
    os.remove(psfile)
    return pdffile


def conv_pcb2gbr(pcbpath):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    gbrfile = os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber', os.path.splitext(pcb_file)[0])
    subprocess.call(['pcb', '-x', 'gerber',
                     '--gerberfile', gbrfile,
                     '--all-layers', '--verbose', '--outline',
                     pcb_file], cwd=pcb_folder)
    return os.path.join(os.path.join(pcb_folder, os.pardir), 'gerber')


def conv_pcb2dxf(pcbpath, pcbname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    dxffile = os.path.splitext(pcbpath)[0] + '.dxf'
    psfile = os.path.splitext(pcbpath)[0] + '.ps'
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--media', 'A4', '--show-legend', '--multi-file',
                     pcb_file], cwd=pcb_folder)
    psfile = os.path.splitext(pcbpath)[0] + '.top.ps'
    subprocess.call(['pstoedit', '-f', 'dxf', psfile, dxffile])
    cleanlist = [f for f in os.listdir(pcb_folder) if f.endswith(".ps")]
    for f in cleanlist:
        os.remove(os.path.join(pcb_folder, f))
    return dxffile
