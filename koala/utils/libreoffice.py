# Copyright (C) 2015 Chintalagiri Shashank
# 
# This file is part of Koala.
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
LibreOffice Utils Module Documentation (:mod:`utils.ooutils`)
=============================================================
"""

from koala.utils.fs import TEMPDIR

import shutil
import os
import subprocess
import atexit

open_files = []


class XLFile(object):
    def __init__(self, filepath):
        self.fpath = filepath
        self.fname = os.path.split(filepath)[1]
        self._csv_list = []
        self._tfpath = self._make_copy()
        self._make_csv_files()

        open_files.append(self)

    def get_csv_path(self, sheetname):
        for (sname, spath) in self._csv_list:
            if sname == sheetname:
                return spath
        return None

    def _make_copy(self):
        tfpath = os.path.join(TEMPDIR, self.fname)
        shutil.copyfile(self.fpath, tfpath)
        return tfpath

    def _make_csv_files(self):
        fname = os.path.splitext(self.fname)[0]
        csvpath = os.path.join(TEMPDIR, fname + '-%s.csv')
        cstrl = ["ssconverter", self._tfpath, csvpath]
        self._csv_list = self._parse_sscout(subprocess.check_output(cstrl))

    def _parse_sscout(self, string):
        fname = os.path.splitext(self.fname)[0]
        rlist = [x.strip() for x in string.split('\n')[1:-1]]
        rlist = [(os.path.split(x)[1][len(fname) + 1:-4], x) for x in rlist]
        return rlist

    def close(self):
        self._clean()
        open_files.remove(self)

    def _clean(self):
        os.remove(self._tfpath)
        for (s, csvpath) in self._csv_list:
            os.remove(csvpath)


def get_xlf(fpath):
    for f in open_files:
        if f.fpath == fpath:
            return f
    f = XLFile(fpath)
    return f


def ooutils_cleanup():
    for f in open_files:
        f.close()

atexit.register(ooutils_cleanup)
