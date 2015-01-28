"""
gEDA BOM Parser module documentation (:mod:`gedaif.bomparser`)
==============================================================
"""

import gedaif.projfile
import gedaif.conffile

import subprocess
import os


class BomLine(object):

    def __init__(self, line, columns):
        self.data = {}
        elems = line.split('\t')
        for i in range(len(columns)):
            self.data[columns[i]] = elems[i]


class GedaBomParser(object):

    def __init__(self, projectfolder, backend, electrical=False):
        self.gpf = None
        self.temp_bom = None
        self.columns = []
        self.line_gen = None
        self.projectfolder = os.path.normpath(projectfolder)
        self._gpf = gedaif.projfile.GedaProjectFile(self.projectfolder, electrical)

        if electrical is True:
            self._basefolder = 'electrical'
        else:
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
                        self.gpf.schpaths)

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
