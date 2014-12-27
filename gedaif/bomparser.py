"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import gedaif.projfile

import subprocess
import os


class BomLine(object):

    data = {}

    def __init__(self, line, columns):
        elems = line.split('\t')
        for i in range(len(columns)):
            self.data[columns[i]] = elems[i]


class GedaBomParser(object):

    gpf = None
    temp_bom = None
    columns = []
    line_gen = None

    def __init__(self, projectfolder, projfile):
        self.load_project_file(projectfolder, projfile)
        self.generate_temp_bom(projectfolder)
        self.prep_temp_bom(projectfolder)

    def load_project_file(self, projectfolder, projfile):
        self.gpf = gedaif.projfile.GedaProjectFile(projectfolder, projfile)

    def generate_temp_bom(self, projectfolder):
        os.chdir(os.path.normpath(projectfolder + "/schematic"))
        cmd = "gnetlist -o tempbom.net -g bom"
        print cmd.split()+self.gpf.schfiles
        subprocess.call(cmd.split() + self.gpf.schfiles)

    def prep_temp_bom(self, projectfolder):
        fname = os.path.normpath(projectfolder + "/schematic/tempbom.net")
        self.temp_bom = open(fname, 'r')
        self.columns = self.temp_bom.readline().split('\t')[:-1]
        self.line_gen = self.get_lines()

    def get_lines(self):
        for line in self.temp_bom:
            yield BomLine(line, self.columns)
        self.temp_bom.close()


