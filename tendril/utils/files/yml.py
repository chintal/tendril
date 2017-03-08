#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for yml
"""

import os
from yaml import load as oload
from yaml import dump as odump

try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader
    from yaml import Dumper

from tendril.utils.fsutils import get_concatenated_fd


def load(f):
    if isinstance(f, str):
        filepaths = []
        if os.path.exists(f) and os.path.isfile(f):
            filepaths.append(f)
        dirpath = f + '.d'
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            dirfiles = [os.path.join(dirpath, x)
                        for x in sorted(os.listdir(dirpath))]
            filepaths.extend([x for x in dirfiles
                              if os.path.isfile(x) and x.endswith('.yaml')])
        if not len(filepaths):
            raise IOError("YAML file not found : {0}".format(f))
        return oload(get_concatenated_fd(filepaths), Loader=Loader)
    else:
        return oload(f, Loader=Loader)


def dump(data, f=None, **kwargs):
    return odump(data, stream=f, Dumper=Dumper, **kwargs)
