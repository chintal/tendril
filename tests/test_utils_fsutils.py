#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for test_utils_fsutils
"""

import os
from fs.base import FS
from fs.osfs import OSFS
from tendril.utils import fsutils


def test_fsutils_tempfs():
    assert os.path.exists(fsutils.TEMPDIR)
    assert os.path.isdir(fsutils.TEMPDIR)
    assert isinstance(fsutils.temp_fs, FS)
    assert isinstance(fsutils.temp_fs, OSFS)
    tempname = fsutils.get_tempname()
    assert isinstance(tempname, str)
    assert not os.path.exists(os.path.join(fsutils.TEMPDIR, tempname))
    # TODO This does not work locally. Figure out why.
    # fsutils.TEMPDIR returns /tmp instead of creating a new tempdir.
    # fsutils.fsutils_cleanup()
    # assert not os.path.exists(fsutils.TEMPDIR)


def test_fsutils_mro():
    # TODO This should be tested alongside reload
    class TestClass1(object):
        pass

    class TestClass2(TestClass1):
        pass

    obj = TestClass2()
    assert fsutils.get_parent(obj) == TestClass1
