"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import boms.electronics


def gen_assemmanifest(projfolder, configname):
    pass


def gen_funcbom(projfolder, configname):
    pass


def gen_configdoc(projfolder):
    pass


def gen_schpdf(projfolder):
    pass


def gen_masterdoc(projfolder):
    gen_schpdf(projfolder)
    gen_configdoc(projfolder)
    # TODO Combine PDFs


def gen_funcpdf(projfolder, configname):
    gen_schpdf(projfolder)
    gen_funcbom(projfolder, configname)
    # TODO Combine PDFs




if __name__ == "__main__":
    pass
