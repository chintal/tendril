"""
gEDA Project File module documentation (:mod:`gedaif.projfile`)
===============================================================
"""

import gedaif.conffile
import os


class GedaProjectFile(object):

    def __init__(self, projectfolder):
        self.schfiles = []
        self.pcbfile = None
        self.schfolder = os.path.join(os.path.abspath(projectfolder), 'schematic')
        configsfile = gedaif.conffile.ConfigsFile(projectfolder)
        projfilepath = os.path.join(projectfolder, 'schematic',
                                    configsfile.configdata['projfile'])
        with open(projfilepath, 'r') as f:
            for line in f:
                line = self.strip_line(line)
                if line != '':
                    parts = line.split('\t')
                    if parts[0].strip() == 'schematics':
                        for part in parts[1].split(' '):
                            self.schfiles.append(part.strip())
                    if parts[0].strip('\t') == 'output-name':
                        self.pcbfile = parts[1].strip().split('/')[-1]

    @staticmethod
    def strip_line(line):
        line = line.split("#")[0]
        return line.strip()

    @property
    def schpaths(self):
        return [os.path.join(self.schfolder, schfile) for schfile in self.schfiles]

if __name__ == "__main__":
    pass
