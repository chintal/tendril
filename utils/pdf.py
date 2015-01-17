"""
PDF Utils Module documentation (:mod:`utils.pdfutils`)
==============================================================

This module contains small helper functions to handle PDF files. These
functions are independent of the rest of the software and can be reused
wherever needed.

"""

import PyPDF2

import os
import subprocess


def merge_pdf(pdflist, outfilepath):
    """
    Merges PDF files.
    Sources are PDF files whose paths are listed in ``pdflist`` and
    the combined PDF is written out to ``outfilepath``.


    :param pdflist: List of paths to PDF files to be merged.
    :param outfilepath: Path where output PDF file is to be written.
    :return: outfilepath
    """
    merger = PyPDF2.PdfFileMerger()
    for f in pdflist:
        f = os.path.normpath(f)
        merger.append(PyPDF2.PdfFileReader(file(f, 'rb')))
        merger.write(outfilepath)
        return outfilepath


def conv_ps2pdf(pspath, pdfpath):
    """
    Runs `ps2pdf` to convert a PS file specified in ``pspath`` to
    a PDF file writen out to ``pdfpath``.

    :param pspath: Path to PS file to be converted.
    :param pdfpath: Path of PDF file to be generated.
    """
    subprocess.call(['ps2pdf', pspath, pdfpath])
