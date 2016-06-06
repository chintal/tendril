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
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""

import os
import re
import subprocess
from collections import deque

import tendril.utils.log

logger = tendril.utils.log.get_logger(__name__, tendril.utils.log.INFO)

from tendril.utils.files import pdf

from tendril.utils.config import GEDA_SCHEME_DIR
from tendril.utils.config import USE_SYSTEM_GAF_BIN
from tendril.utils.config import GAF_BIN_ROOT

import sym2eps


def conv_gsch2pdf(schpath, docfolder):
    schpath = os.path.normpath(schpath)
    schfname = os.path.splitext(os.path.split(schpath)[1])[0]
    pspath = os.path.join(docfolder, schfname + '.ps')
    pdfpath = os.path.join(docfolder, schfname + '.pdf')
    # TODO fix this
    if USE_SYSTEM_GAF_BIN:
        gschem_pscmd = "gschem -o" + pspath + \
                       " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
        subprocess.call(gschem_pscmd.split(' '))
        pdf.conv_ps2pdf(pspath, pdfpath)
        os.remove(pspath)
    else:
        gaf_pdfcmd = [os.path.join(GAF_BIN_ROOT, 'gaf'),
                      'export', '-o', pdfpath,
                      schpath]
        subprocess.call(gaf_pdfcmd)
    return pdfpath


def conv_gsch2png(schpath, outfolder, include_extension=False):
    schpath = os.path.normpath(schpath)
    if include_extension is False:
        schfname, ext = os.path.splitext(os.path.split(schpath)[1])
    else:
        schfname = os.path.split(schpath)[1]

    outpath = os.path.join(outfolder, schfname + '.png')
    epspath = os.path.join(outfolder, schfname + '.eps')

    if USE_SYSTEM_GAF_BIN:
        try:
            sym2eps.convert(schpath, epspath)
        except RuntimeError:
            logger.error(
                "SYM2EPS Segmentation Fault on symbol : " + schpath
            )
        gschem_pngcmd = [
            "convert", epspath, "-transparent", "white", outpath
        ]
        subprocess.call(gschem_pngcmd)
        try:
            os.remove(epspath)
        except OSError:
            logger.warning("Temporary .eps file not found to remove : " +
                           epspath)
    else:
        gaf_pngcmd = [
            os.path.join(GAF_BIN_ROOT, 'gaf'),
            'export', '-c', '-o', outpath,
            schpath
        ]
        subprocess.call(gaf_pngcmd)
    return outpath


if __name__ == "__main__":
    pass
