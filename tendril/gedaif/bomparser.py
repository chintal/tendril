# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
gEDA BOM Parser module documentation (:mod:`gedaif.bomparser`)
==============================================================
"""

import subprocess
import os
import shutil

from tendril.conventions.motifs import create_motif_object

import projfile

from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.fsutils import TEMPDIR
from tendril.utils import log
logger = log.get_logger(__name__, level=log.WARNING)


FNULL = open(os.devnull, 'w')


class BomLine(object):

    def __init__(self, line, columns):
        self.data = {}
        elems = line.split('\t')
        for i in range(len(columns)):
            self.data[columns[i]] = elems[i]

    def __repr__(self):
        return self.data.__repr__()


class GedaBomParser(object):

    def __init__(self, projectfolder, backend):
        self.gpf = None
        self.temp_bom = None
        self.columns = []
        self.line_gen = None
        self.projectfolder = os.path.normpath(projectfolder)
        self._gpf = projfile.GedaProjectFile(self.projectfolder)

        self._namebase = os.path.relpath(self.projectfolder, PROJECTS_ROOT)
        self._basefolder = 'schematic'

        self._temp_folder = os.path.join(TEMPDIR, self._namebase,
                                         self._basefolder)
        self._temp_bom_path = os.path.join(self._temp_folder,
                                           "tempbom.net")
        self._get_temp_schematic()
        self._transform_schematic()
        self.generate_temp_bom(backend)
        self.prep_temp_bom()

    def _get_temp_schematic(self):
        self.schpaths = []
        if not os.path.exists(self._temp_folder):
            os.makedirs(self._temp_folder)
        for schpath in self._gpf.schpaths:
            tschpath = os.path.join(self._temp_folder,
                                    os.path.split(schpath)[1])
            shutil.copy(schpath, tschpath)
            self.schpaths.append(tschpath)

    def _transform_schematic(self):
        pass

    def generate_temp_bom(self, backend):
        cmd = ["gnetlist",
               '-o', self._temp_bom_path,
               '-g', backend,
               '-Oattrib_file=' + os.path.join(self.projectfolder,
                                               self._basefolder,
                                               'attribs')
               ]
        cmd.extend(self.schpaths)
        subprocess.call(cmd,
                        stdout=FNULL,
                        stderr=subprocess.STDOUT,)

    def prep_temp_bom(self):
        self.temp_bom = open(self._temp_bom_path, 'r')
        self.columns = self.temp_bom.readline().split('\t')[:-1]
        self.line_gen = self.get_lines()

    def delete_temp_bom(self):
        os.remove(self._temp_bom_path)
        for tschpath in self.schpaths:
            os.remove(tschpath)

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
        logger.info("Creating new motif : " + motifst)
        try:
            motif = create_motif_object(motifst)
            self._motifs.append(motif)
        except ValueError:
            logger.error("Failed to create motif : " + motifst)
            motif = None
        return motif

    def get_lines(self):
        for line in self.temp_bom:
            bomline = BomLine(line, self.columns)
            if bomline.data['motif'] != 'unknown':
                logger.debug("Found motif element : " + bomline.data['motif'])
                motif = self.get_motif(bomline.data['motif'])
                if motif is not None:
                    motif.add_element(bomline)
                else:
                    logger.warning(
                        "Element not inserted : " + bomline.data["refdes"]
                    )
            else:
                yield bomline
        self.motif_gen = self.get_motifs()
        self.temp_bom.close()
        self.delete_temp_bom()

    def get_motifs(self):
        for motif in self._motifs:
            yield motif
