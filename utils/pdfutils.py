"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from PyPDF2 import PdfFileReader, PdfFileMerger

import os
import subprocess


def merge_pdf(pdflist, outfilepath):
    merger = PdfFileMerger()
    for f in pdflist:
        f = os.path.normpath(f)
        merger.append(PdfFileReader(file(f, 'rb')))
        merger.write(outfilepath)
        return outfilepath


def conv_ps2pdf(pspath, pdfpath):
    subprocess.call(['ps2pdf', pspath, pdfpath])


renderer_pdf = jinja2_pdfinit()
