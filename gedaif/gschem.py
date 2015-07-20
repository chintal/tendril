"""
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""


from utils.config import GEDA_SCHEME_DIR
import utils.pdf

import os
import subprocess


def conv_gsch2pdf(schpath, docfolder):
    schpath = os.path.normpath(schpath)
    schfname = os.path.splitext(os.path.split(schpath)[1])[0]
    pspath = os.path.join(docfolder, schfname + '.ps')
    pdfpath = os.path.join(docfolder, schfname + '.pdf')
    gschem_pscmd = "gschem -o" + pspath + " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
    subprocess.call(gschem_pscmd.split(' '))
    utils.pdf.conv_ps2pdf(pspath, pdfpath)
    os.remove(pspath)
    return pdfpath


def conv_gsch2png(schpath, outfolder):
    schpath = os.path.normpath(schpath)
    schfname = os.path.splitext(os.path.split(schpath)[1])[0]
    outpath = os.path.join(outfolder, schfname + '.png')
    gschem_pngcmd = "gschem -p -o" + outpath + " -s" + GEDA_SCHEME_DIR + '/image.scm ' + schpath
    subprocess.call(gschem_pngcmd.split(' '))
    return outpath


if __name__ == "__main__":
    pass
