"""
gEDA Project Dox module documentation (:mod:`dox.gedaproject`)
==============================================================
"""
import utils.log
logger = utils.log.get_logger(__name__, utils.log.INFO)

import os
import csv

import gedaif.gschem
import gedaif.conffile
import gedaif.projfile
import gedaif.pcb

import utils.pdf
import utils.zip
import utils.fs
import projects
import boms.electronics
import boms.outputbase

import render


def gen_confbom(projfolder, configname):
    gpf = gedaif.projfile.GedaProjectFile(projfolder)
    sch_mtime = utils.fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    outpath = os.path.join(docfolder, 'confdocs', configname + '-bom.pdf')
    outf_mtime = utils.fs.get_file_mtime(outpath)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.info('Skipping up-to-date ' + outpath)
        return outpath

    logger.info('Regenerating ' + outpath + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))
    bom = boms.electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

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
    gpf = gedaif.projfile.GedaProjectFile(projfolder)
    sch_mtime = utils.fs.get_folder_mtime(gpf.schfolder)

    configfile = gedaif.conffile.ConfigsFile(projfolder)
    docfolder = projects.get_project_doc_folder(projfolder)

    schpdfpath = os.path.join(docfolder, namebase + '-schematic.pdf')
    outf_mtime = utils.fs.get_file_mtime(schpdfpath)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.info('Skipping up-to-date ' + schpdfpath)
        return schpdfpath

    logger.info('Regenerating ' + schpdfpath + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    if configfile.configdata is not None:
        pdffiles = []
        for schematic in gpf.schfiles:
            schfile = os.path.normpath(projfolder + '/schematic/' + schematic)
            pdffile = gedaif.gschem.conv_gsch2pdf(schfile, docfolder)
            pdffiles.append(pdffile)
        utils.pdf.merge_pdf(pdffiles, schpdfpath)
        for pdffile in pdffiles:
            os.remove(pdffile)
        return schpdfpath


def gen_masterdoc(projfolder, namebase):
    gpf = gedaif.projfile.GedaProjectFile(projfolder)
    sch_mtime = utils.fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    masterdocfile = os.path.join(docfolder, namebase + '-masterdoc.pdf')
    outf_mtime = utils.fs.get_file_mtime(masterdocfile)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.info('Skipping up-to-date ' + masterdocfile)
        return masterdocfile

    logger.info('Regnerating ' + masterdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_configdoc(projfolder, namebase),
                gen_schpdf(projfolder, namebase)]

    utils.pdf.merge_pdf(pdffiles, masterdocfile)
    return masterdocfile


def gen_confpdf(projfolder, configname, namebase):
    gpf = gedaif.projfile.GedaProjectFile(projfolder)
    sch_mtime = utils.fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    confdocfile = os.path.join(docfolder, 'confdocs', configname + '-doc.pdf')
    outf_mtime = utils.fs.get_file_mtime(confdocfile)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.info('Skipping up-to-date ' + confdocfile)
        return confdocfile

    logger.info('Regenerating ' + confdocfile + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    pdffiles = [gen_confbom(projfolder, configname),
                gen_schpdf(projfolder, namebase)]
    utils.pdf.merge_pdf(pdffiles, confdocfile)
    return confdocfile


def gen_cobom_csv(projfolder, namebase):
    gpf = gedaif.projfile.GedaProjectFile(projfolder)
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    sch_mtime = utils.fs.get_folder_mtime(gpf.schfolder)

    docfolder = projects.get_project_doc_folder(projfolder)
    cobom_csv_path = os.path.join(docfolder, 'confdocs', 'conf-boms.csv')
    outf_mtime = utils.fs.get_file_mtime(cobom_csv_path)

    if outf_mtime is not None and outf_mtime > sch_mtime:
        logger.info('Skipping up-to-date ' + cobom_csv_path)
        return cobom_csv_path

    logger.info('Regenerating ' + cobom_csv_path + os.linesep +
                'Last modified : ' + str(sch_mtime) + '; Last Created : ' + str(outf_mtime))

    bomlist = []
    for cfn in configfile.configdata['configurations']:
        gen_confpdf(projfolder, cfn['configname'], namebase)
        lbom = boms.electronics.import_pcb(projfolder)
        lobom = lbom.create_output_bom(cfn['configname'])
        bomlist.append(lobom)
    cobom = boms.outputbase.CompositeOutputBom(bomlist)

    with open(cobom_csv_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['device'] + [x.configname for x in cobom.descriptors])
        for line in cobom.lines:
            writer.writerow([line.ident] + line.columns)


def gen_pcb_pdf(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    gpf = gedaif.projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = utils.fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    docfolder = projects.get_project_doc_folder(projfolder)
    pdffile = os.path.join(docfolder, configfile.configdata['pcbname']+'-pcb.pdf')
    outf_mtime = utils.fs.get_file_mtime(pdffile)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.info('Skipping up-to-date ' + pdffile)
        return pdffile

    logger.info('Regenerating ' + pdffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime) + ' ' + str(outf_mtime > pcb_mtime))

    pdffile = gedaif.pcb.conv_pcb2pdf(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
                                      docfolder, configfile.configdata['pcbname'])
    return pdffile


def gen_pcb_gbr(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    gpf = gedaif.projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = utils.fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    gbrfolder = os.path.join(configfile.projectfolder, 'gerber')
    outf_mtime = utils.fs.get_folder_mtime(gbrfolder)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.info('Skipping up-to-date ' + gbrfolder)
        return gbrfolder

    logger.info('Regenerating ' + gbrfolder + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime))

    gbrfolder = gedaif.pcb.conv_pcb2gbr(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    zfile = os.path.join(projfolder, gpf.pcbfile + '-gerber.zip')
    utils.zip.zipdir(gbrfolder, zfile)
    return gbrfolder


def gen_pcb_dxf(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    gpf = gedaif.projfile.GedaProjectFile(configfile.projectfolder)
    pcb_mtime = utils.fs.get_file_mtime(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'))
    dxffile = os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.dxf')
    outf_mtime = utils.fs.get_file_mtime(dxffile)

    if outf_mtime is not None and outf_mtime > pcb_mtime:
        logger.info('Skipping up-to-date ' + dxffile)
        return dxffile

    logger.info('Regenerating ' + dxffile + os.linesep +
                'Last modified : ' + str(pcb_mtime) + '; Last Created : ' + str(outf_mtime))
    dxffile = gedaif.pcb.conv_pcb2dxf(os.path.join(configfile.projectfolder, 'pcb', gpf.pcbfile + '.pcb'),
                                      configfile.configdata['pcbname'])
    return dxffile


def generate_docs(projfolder):
    configfile = gedaif.conffile.ConfigsFile(projfolder)
    namebase = configfile.configdata['pcbname']
    gen_masterdoc(projfolder, namebase)

    gen_cobom_csv(projfolder, namebase)
    gen_pcb_pdf(projfolder)
    gen_pcb_gbr(projfolder)
    gen_pcb_dxf(projfolder)


if __name__ == "__main__":
    pass
