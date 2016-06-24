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
import subprocess

from tendril.utils.files import pdf
from tendril.utils import log

logger = log.get_logger(__name__, log.INFO)


def get_pcbinfo(pcbpath):
    raise NotImplementedError


def conv_pcb2pdf(pcbpath, docfolder, projname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    psfile = os.path.join(docfolder, projname + '-pcb.ps')
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--outline', '--media', 'A4', '--show-legend',
                     pcb_file], cwd=pcb_folder)
    pdffile = os.path.join(docfolder, projname + '-pcb.pdf')
    pdf.conv_ps2pdf(psfile, pdffile)
    os.remove(psfile)
    return pdffile


def conv_pcb2gbr(pcbpath, outfolder):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    gbrfile = os.path.join(outfolder, os.path.splitext(pcb_file)[0])
    subprocess.call(['pcb', '-x', 'gerber',
                     '--gerberfile', gbrfile,
                     '--all-layers', '--verbose', '--outline',
                     pcb_file], cwd=pcb_folder)
    return outfolder


def conv_pcb2dxf(pcbpath, outfolder, pcbname):
    pcb_folder, pcb_file = os.path.split(pcbpath)
    dxffile = os.path.join(outfolder, pcbname + '.dxf')
    psfile = os.path.join(outfolder, pcbname + '.ps')
    subprocess.call(['pcb', '-x', 'ps',
                     '--psfile', psfile,
                     '--media', 'A4', '--show-legend', '--multi-file',
                     pcb_file], cwd=pcb_folder)
    psfile = os.path.join(outfolder, pcbname + '.top.ps')
    bottom_psfile = os.path.join(outfolder, pcbname + '.bottom.ps')
    bottom_dxffile = os.path.join(outfolder, pcbname + 'bottom.dxf')
    subprocess.call(['pstoedit', '-f', 'dxf', psfile, dxffile])
    subprocess.call(['pstoedit', '-f', 'dxf', bottom_psfile, bottom_dxffile])
    cleanlist = [f for f in os.listdir(outfolder) if f.endswith(".ps")]
    for f in cleanlist:
        os.remove(os.path.join(outfolder, f))
    return dxffile
