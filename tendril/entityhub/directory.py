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
Docstring for directory
"""

from tendril.gedaif import gsymlib


def in_gsymlib(ident):
    return gsymlib.is_recognized(ident)


def gsymlib_idents():
    return gsymlib.gsymlib_idents


def in_pcblib(ident):
    pass


def in_prototypelib(ident):
    pass


def is_project_folder(projfolder):
    pass


def is_recognized(ident):
    if in_gsymlib(ident):
        return True
    if in_prototypelib(ident):
        return True
    if in_pcblib(ident):
        return True
    return False
