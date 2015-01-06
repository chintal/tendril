"""
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""


from utils.config import GEDA_SCHEME_DIR
import utils.pdfutils

import os
import subprocess


def conv_gsch2pdf(schpath):
    schpath = os.path.normpath(schpath)
    pspath = os.path.normpath(os.path.splitext(schpath)[0]+'.ps')
    pdfpath = os.path.normpath(os.path.splitext(schpath)[0]+'.pdf')
    gschem_pscmd = "gschem -o" + pspath + " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
    subprocess.call(gschem_pscmd.split(' '))
    utils.pdfutils.conv_ps2pdf(pspath, pdfpath)
    os.remove(pspath)
    return pdfpath


if __name__ == "__main__":
    pass
