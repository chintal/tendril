"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
import subprocess

from __init__ import GEDA_SCHEME_DIR
import projfile


def conv_gsch2pdf(schpath):
    schpath = os.path.normpath(schpath)
    pdfpath = os.path.normpath(os.path.splitext(schpath)[0]+'.pdf')
    gschem_pdfcmd = "gschem -o" + pdfpath + " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
    subprocess.call(gschem_pdfcmd.split(' '))
    return pdfpath


def gen_schpdf(projpath):


if __name__ == "__main__":
    pass
