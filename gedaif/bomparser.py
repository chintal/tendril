"""
gEDA BOM Parser module documentation (:mod:`gedaif.bomparser`)
==============================================================
"""

import subprocess
import os

import logging
logging.basicConfig(level=logging.DEBUG)


from conventions.motifs import create_motif_object


import gedaif.projfile
import gedaif.conffile


class BomLine(object):

    def __init__(self, line, columns):
        self.data = {}
        elems = line.split('\t')
        for i in range(len(columns)):
            self.data[columns[i]] = elems[i]


class GedaBomParser(object):

    def __init__(self, projectfolder, backend):
        self.gpf = None
        self.temp_bom = None
        self.columns = []
        self.line_gen = None
        self.projectfolder = os.path.normpath(projectfolder)
        self._gpf = gedaif.projfile.GedaProjectFile(self.projectfolder)

        self._basefolder = 'schematic'

        self._temp_bom_path = os.path.join(self.projectfolder, self._basefolder, "tempbom.net")
        self.generate_temp_bom(backend)
        self.prep_temp_bom()

    def generate_temp_bom(self, backend):
        cmd = "gnetlist"
        subprocess.call(cmd.split() +
                        ['-o', self._temp_bom_path] +
                        ['-g', backend] +
                        ['-Oattrib_file='+os.path.join(self.projectfolder, self._basefolder, 'attribs')] +
                        self._gpf.schpaths)

    def prep_temp_bom(self):
        self.temp_bom = open(self._temp_bom_path, 'r')
        self.columns = self.temp_bom.readline().split('\t')[:-1]
        self.line_gen = self.get_lines()

    def delete_temp_bom(self):
        os.remove(self._temp_bom_path)

    def get_lines(self):
        for line in self.temp_bom:
            yield BomLine(line, self.columns)
        self.temp_bom.close()
        self.delete_temp_bom()


class MotifAwareBomParser(GedaBomParser):
    def __init__(self, projectfolder, backend):
        super(MotifAwareBomParser, self).__init__(projectfolder, backend)
        self._motifs = []
        # self._motifconfigs = self._gpf.configsfile.configdata['motiflist']
        self.motif_gen = None

    def get_motif(self, motifst):
        motifst = motifst.split(':')[0]
        for motif in self._motifs:
            if motif.refdes == motifst:
                return motif
        logging.debug("Creating new motif : " + motifst)
        motif = create_motif_object(motifst)
        self._motifs.append(motif)
        return motif

    def get_lines(self):
        for line in self.temp_bom:
            bomline = BomLine(line, self.columns)
            if bomline.data['motif'] != 'unknown':
                logging.debug("Found motif element : " + bomline.data['motif'])
                motif = self.get_motif(bomline.data['motif'])
                motif.add_element(bomline)
            else:
                yield bomline
        self.motif_gen = self.get_motifs()
        self.temp_bom.close()
        self.delete_temp_bom()

    def get_motifs(self):
        for motif in self._motifs:
            yield motif
