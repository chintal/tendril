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
from six import string_types
from six import integer_types

try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader
    from yaml import Dumper

from tendril.utils.fsutils import get_concatenated_fd

try:
  basestring
except NameError:
  basestring = str


class YamlReaderError(Exception):
    pass


def data_merge(a, b):
    """
    From https://github.com/ImmobilienScout24/yamlreader/blob/master/src/main/python/yamlreader/yamlreader.py
    merges b into a and return merged result based on
    http://stackoverflow.com/questions/7204805/python-dictionaries-of-dictionaries-merge
    and extended to also merge arrays and to replace the content of keys
    with the same name.

    NOTE: tuples and arbitrary objects are not handled as it is totally
    ambiguous what should happen
    """
    key = None

    try:
        if a is None or isinstance(a, (string_types, float, integer_types)):
            # border case for first run or if a is a primitive
            a = b
        elif isinstance(a, list):
            # lists can be only appended
            if isinstance(b, list):
                # merge lists
                a.extend(b)
            else:
                # append to list
                a.append(b)
        elif isinstance(a, dict):
            # dicts must be merged
            if isinstance(b, dict):
                for key in b:
                    if key in a:
                        a[key] = data_merge(a[key], b[key])
                    else:
                        a[key] = b[key]
            else:
                raise YamlReaderError(
                    'Cannot merge non-dict "%s" into dict "%s"' % (b, a))
        else:
            raise YamlReaderError('NOT IMPLEMENTED "%s" into "%s"' % (b, a))
    except TypeError as e:
        raise YamlReaderError(
            'TypeError "%s" in key "%s" when merging "%s" into "%s"' % (
            e, key, b, a))

    return a


def load_yamls(filepaths):
    if not len(filepaths):
        return
    rval = None
    for filepath in filepaths:
        with open(filepath, 'r') as f:
            rval = data_merge(rval, oload(f, Loader=Loader))
    return rval


def load(f, method='merge'):
    if isinstance(f, basestring):
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
        if method == 'concat':
            return oload(get_concatenated_fd(filepaths), Loader=Loader)
        elif method == 'merge':
            return load_yamls(filepaths)
    else:
        return oload(f, Loader=Loader)


def dump(data, f=None, **kwargs):
    return odump(data, stream=f, Dumper=Dumper, **kwargs)
