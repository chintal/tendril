"""
gEDA Project Dox module documentation (:mod:`dox.gedaproject`)
==============================================================
"""

import gedaif.gschem
import gedaif.conffile
import gedaif.projfile
import utils.pdf

import os


def gen_confbom(projfolder, configname):
    pass


def gen_configdoc(projfolder):
    pass


def gen_schpdf(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    if configfile.configdata is not None:
        gpf = gedaif.projfile.GedaProjectFile(configfile.projectfolder)
        pdffiles = []
        for schematic in gpf.schfiles:
            schfile = os.path.normpath(projfolder + '/schematic/' + schematic)
            pdffile = gedaif.gschem.conv_gsch2pdf(schfile)
            pdffiles.append(pdffile)
        schpdfpath = os.path.normpath(configfile.projectfolder+"/schematic/schematic.pdf")
        utils.pdf.merge_pdf(pdffiles, schpdfpath)
        for pdffile in pdffiles:
            os.remove(pdffile)
        return schpdfpath


def gen_masterdoc(projfolder):
    pdffiles = [gen_configdoc(projfolder), gen_schpdf(projfolder)]
    masterdocfile = os.path.normpath(projfolder+"/schematic/sch-master.pdf")
    utils.pdf.merge_pdf(pdffiles, masterdocfile)
    return masterdocfile


def gen_confpdf(projfolder, configname):
    pdffiles = [gen_confbom(projfolder, configname), gen_schpdf(projfolder)]
    confdocfile = os.path.normpath(projfolder+"/schematic/sch-" + configname + ".pdf")
    utils.pdf.merge_pdf(pdffiles, confdocfile)
    return confdocfile


if __name__ == "__main__":
    pass
