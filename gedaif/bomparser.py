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

    def __init__(self, projectfolder, backend):
        self.gpf = None
        self.temp_bom = None
        self.columns = []
        self.line_gen = None
        self.projectfolder = projectfolder
        self.gpf = gedaif.projfile.GedaProjectFile(self.projectfolder)
        self.generate_temp_bom(backend)
        self.prep_temp_bom()

    def generate_temp_bom(self, backend):
        os.chdir(os.path.normpath(self.projectfolder + "/schematic"))
        cmd = "gnetlist -o tempbom.net -g"
        subprocess.call(cmd.split() + [backend] + self.gpf.schfiles)

    def prep_temp_bom(self):
        fname = os.path.normpath(self.projectfolder + "/schematic/tempbom.net")
        self.temp_bom = open(fname, 'r')
        self.columns = self.temp_bom.readline().split('\t')[:-1]
        self.line_gen = self.get_lines()

    def delete_temp_bom(self):
        fpath = os.path.normpath(self.projectfolder + "/schematic/tempbom.net")
        os.remove(fpath)

    def get_lines(self):
        for line in self.temp_bom:
            yield BomLine(line, self.columns)
        self.temp_bom.close()
        self.delete_temp_bom()


