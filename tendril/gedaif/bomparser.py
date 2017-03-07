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
gEDA BOM Parser Module (:mod:`tendril.gedaif.bomparser`)
========================================================
"""

import subprocess
import csv
import os
import shutil

from tendril.conventions.motifs import create_motif_object
from tendril.conventions.electronics import ident_transform
from tendril.boms.validate import ValidationContext
from tendril.boms.validate import ErrorCollector
from tendril.boms.validate import BomMotifPolicy
from tendril.boms.validate import BomMotifUnrecognizedError

import projfile

from tendril.utils.config import INSTANCE_CACHE
from tendril.utils.config import PROJECTS_ROOT
from tendril.utils import fsutils
from tendril.utils import log
logger = log.get_logger(__name__, level=log.WARNING)


FNULL = open(os.devnull, 'w')


class BomLine(object):

    def __init__(self, line, columns):
        self.data = {}
        line = line.rstrip('\r\n')
        elems = line.split('\t')
        for i in range(len(columns)):
            self.data[columns[i]] = elems[i]

    def __repr__(self):
        return self.data.__repr__()

    def __getattr__(self, item):
        if item in self.data.keys():
            return self.data[item]
        elif item == 'ident':
            return ident_transform(
                self.data['device'],
                self.data['value'],
                self.data['footprint']
            )
        else:
            raise AttributeError


class CachedBomParser(object):
    _basefolder = None

    def __init__(self, projectfolder, use_cached=True, **kwargs):
        self.projectfolder = os.path.normpath(projectfolder)
        self._namebase = os.path.relpath(self.projectfolder, PROJECTS_ROOT)
        self._validation_context = ValidationContext(
            self.projectfolder, 'BOMParser'
        )
        self._validation_errors = ErrorCollector()
        self.line_gen = None
        self._use_cached = use_cached
        self._generator_args = kwargs

    @property
    def _temp_folder(self):
        return os.path.join(fsutils.TEMPDIR, self._namebase, self._basefolder)

    @property
    def _temp_bom_path(self):
        return os.path.join(self._temp_folder, "tempbom.net")

    @property
    def _cache_folder(self):
        return os.path.join(INSTANCE_CACHE, 'gedaproject', self._namebase)

    @property
    def _cached_bom_path(self):
        return os.path.join(self._cache_folder, 'bom.net')

    def generate_bom_file(self, outfile, **kwargs):
        raise NotImplementedError

    def get_bom_file(self):
        if not os.path.exists(self._cache_folder):
            os.makedirs(self._cache_folder)

        bom_mtime = fsutils.get_file_mtime(self._cached_bom_path)
        source_folder = os.path.join(self.projectfolder, self._basefolder)
        source_mtime = fsutils.get_folder_mtime(source_folder)

        if self._use_cached is True and bom_mtime is not None \
                and source_mtime < bom_mtime:
            return open(self._cached_bom_path, 'r')
        else:
            self.generate_bom_file(self._temp_bom_path,
                                   **self._generator_args)
            shutil.copy(self._temp_bom_path, self._cached_bom_path)
            return open(self._cached_bom_path, 'r')

    def get_lines(self):
        raise NotImplementedError

    @property
    def validation_errors(self):
        return self._validation_errors


class GedaBomParser(CachedBomParser):
    _basefolder = 'schematic'

    def __init__(self, projectfolder, use_cached=True, backend=None):
        super(GedaBomParser, self).__init__(projectfolder,
                                            use_cached=use_cached,
                                            backend=backend)
        self._gpf = projfile.GedaProjectFile(self.projectfolder)
        self.bom_reader = None
        self.columns = []
        self.schpaths = []
        self.prep_bom()

    def _get_temp_schematic(self):
        self.schpaths = []
        if not os.path.exists(self._temp_folder):
            os.makedirs(self._temp_folder)
        for schpath in self._gpf.schpaths:
            tschpath = os.path.join(self._temp_folder,
                                    os.path.split(schpath)[1])
            shutil.copy(schpath, tschpath)
            self.schpaths.append(tschpath)

    def generate_bom_file(self, outpath, backend=None):
        self._get_temp_schematic()
        cmd = ["gnetlist",
               '-g', backend,
               '-Oattrib_file=' + os.path.join(self.projectfolder,
                                               self._basefolder,
                                               'attribs')
               ]
        outdir, outfile = os.path.split(outpath)
        idx_refdes = None
        idx_schfile = None
        intermediate_outpath = os.path.join(outdir, 'int.' + outfile)
        with open(intermediate_outpath, 'wb') as outf:
            outw = csv.writer(outf, delimiter='\t')
            header_written = False
            found_refdes = set()
            additional_schfiles = {}
            for schpath in self.schpaths:
                schfile = os.path.split(schpath)[1]
                soutpath = os.path.join(outdir, '.'.join([schfile, outfile]))
                scmd = cmd + ['-o', soutpath, schpath]
                subprocess.call(scmd,
                                stdout=FNULL,
                                stderr=subprocess.STDOUT,)
                with open(soutpath, 'rb') as sf:
                    sr = csv.reader(sf, delimiter='\t')
                    if not header_written:
                        header = next(sr) + ['schfile']
                        outw.writerow(header)
                        idx_refdes = header.index('refdes')
                        idx_schfile = header.index('schfile')
                        header_written = True
                    else:
                        next(sr)
                    for row in sr:
                        refdes = row[idx_refdes]
                        if refdes not in found_refdes:
                            found_refdes.add(refdes)
                            outw.writerow(row + [schfile])
                        else:
                            if refdes in additional_schfiles.keys():
                                additional_schfiles[refdes].append(schfile)
                            else:
                                additional_schfiles[refdes] = [schfile]
        if len(additional_schfiles.keys()):
            with open(intermediate_outpath, 'rb') as inf:
                r = csv.reader(inf, delimiter='\t')
                with open(outpath, 'wb') as outf:
                    w = csv.writer(outf, delimiter='\t')
                    for row in r:
                        if row[idx_refdes] in additional_schfiles.keys():
                            files = [row[idx_schfile]]
                            files.extend(additional_schfiles[row[idx_refdes]])
                            row[idx_schfile] = ';'.join(files)
                        w.writerow(row)
        else:
            shutil.copy(intermediate_outpath, outpath)
        return outpath

    def prep_bom(self):
        self.bom_reader = self.get_bom_file()
        self.columns = self.bom_reader.readline().rstrip().split('\t')
        self.line_gen = self.get_lines()

    def get_lines(self):
        for line in self.bom_reader:
            yield BomLine(line, self.columns)
        self.cleanup()

    def cleanup(self):
        self.bom_reader.close()
        if os.path.exists(self._temp_bom_path):
            os.remove(self._temp_bom_path)
        for tschpath in self.schpaths:
            os.remove(tschpath)


class MotifAwareBomParser(GedaBomParser):
    def __init__(self, projectfolder, **kwargs):
        super(MotifAwareBomParser, self).__init__(projectfolder, **kwargs)
        self._motifs = []
        # self._motifconfigs = self._gpf.configsfile.configdata['motiflist']
        self.motif_gen = None
        self._motif_policy = BomMotifPolicy(self._validation_context)

    def get_motif(self, motifst):
        motifst = motifst.split(':')[0]
        for motif in self._motifs:
            if motif.refdes == motifst:
                return motif
        logger.info("Creating new motif : " + motifst)
        motif = create_motif_object(motifst)
        self._motifs.append(motif)
        return motif

    def get_lines(self):
        for line in self.bom_reader:
            bomline = BomLine(line, self.columns)
            if bomline.data['motif'] != 'unknown':
                try:
                    motif = self.get_motif(bomline.data['motif'])
                    motif.add_element(bomline)
                except ValueError:
                    e = BomMotifUnrecognizedError(self._motif_policy,
                                                  bomline.data['motif'],
                                                  bomline.data['refdes'])
                    self._validation_errors.add(e)
            else:
                yield bomline
        self.motif_gen = self.get_motifs()
        self.cleanup()

    def get_motifs(self):
        for motif in self._motifs:
            yield motif
