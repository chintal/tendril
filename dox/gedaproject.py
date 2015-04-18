"""
gEDA Project Dox module documentation (:mod:`dox.gedaproject`)
==============================================================
"""
import os

import gedaif.gschem
import gedaif.conffile
import gedaif.projfile
import utils.pdf
import projects
import boms.electronics

import render


def gen_confbom(projfolder, configname):
    bom = boms.electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)
    docfolder = projects.get_project_doc_folder(projfolder)
    outpath = os.path.join(docfolder, 'confdocs', configname + '-bom.pdf')
    stage = {'configname': obom.descriptor.configname,
             'pcbname': obom.descriptor.pcbname,
             'lines': obom.lines}
    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'geda-bom-simple.tex'

    render.render_pdf(stage, template, outpath)
    return outpath


def gen_configdoc(projfolder, namebase):
    pass


def gen_schpdf(projfolder, namebase):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    docfolder = projects.get_project_doc_folder(projfolder)
    if configfile.configdata is not None:
        gpf = gedaif.projfile.GedaProjectFile(configfile.projectfolder)
        pdffiles = []
        for schematic in gpf.schfiles:
            schfile = os.path.normpath(projfolder + '/schematic/' + schematic)
            pdffile = gedaif.gschem.conv_gsch2pdf(schfile, docfolder)
            pdffiles.append(pdffile)
        schpdfpath = os.path.join(docfolder, namebase + '-schematic.pdf')
        utils.pdf.merge_pdf(pdffiles, schpdfpath)
        for pdffile in pdffiles:
            os.remove(pdffile)
        return schpdfpath


def gen_masterdoc(projfolder, namebase):
    docfolder = projects.get_project_doc_folder(projfolder)
    pdffiles = [gen_configdoc(projfolder, namebase),
                gen_schpdf(projfolder, namebase)]
    masterdocfile = os.path.join(docfolder, namebase + '-masterdoc.pdf')
    utils.pdf.merge_pdf(pdffiles, masterdocfile)
    return masterdocfile


def gen_confpdf(projfolder, configname, namebase):
    docfolder = projects.get_project_doc_folder(projfolder)
    pdffiles = [gen_confbom(projfolder, configname),
                gen_schpdf(projfolder, namebase)]
    confdocfile = os.path.join(docfolder, 'confdocs', configname + '-doc.pdf')
    utils.pdf.merge_pdf(pdffiles, confdocfile)
    return confdocfile


def generate_docs(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    namebase = configfile.configdata['pcbname']
    gen_masterdoc(projfolder, namebase)
    for cfn in configfile.configdata['configurations']:
        gen_confpdf(projfolder, cfn['configname'], namebase)


if __name__ == "__main__":
    pass
