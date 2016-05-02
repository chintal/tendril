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
gedaif.gsymlib Profiling
------------------------

This file runs profiling on :mod:`tendril.gedaif.gsymlib`.
"""

import os
import inspect

from ..profiler import do_profile

from tendril.entityhub import modules

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'modules'), 'modules')
def generate_prototypelib():
    """
    Profiles the prototype library generation.

    When the ``gsymlib`` module is loaded, it automatically generates the gEDA symbol
    library from the library on the filesystem. This function profiles the generation of
    the symlib.

    :download:`Raw execution profile <../../../profiling/gedaif/gsymlib/gsymlib.profile>`
    :download:`SVG of execution profile <../../../profiling/gedaif/gsymlib/gsymlib.profile.svg>`

    .. rubric:: Execution Profile

    .. image:: ../../../profiling/gedaif/gsymlib/gsymlib.profile.svg

    .. rubric:: pstats Output

    .. literalinclude:: ../../../profiling/gedaif/gsymlib/gsymlib.profile.stats

    """
    return modules.get_prototype_lib(regen=True)


@do_profile(os.path.join(SCRIPT_FOLDER, 'modules'), 'modules_thick')
def generate_thick_prototypelib():
    """
    Profiles the prototype library generation with full object instantiation.

    When the ``gsymlib`` module is loaded, it automatically generates the gEDA symbol
    library from the library on the filesystem. This function profiles the generation of
    the symlib.

    :download:`Raw execution profile <../../../profiling/gedaif/gsymlib/gsymlib.profile>`
    :download:`SVG of execution profile <../../../profiling/gedaif/gsymlib/gsymlib.profile.svg>`

    .. rubric:: Execution Profile

    .. image:: ../../../profiling/gedaif/gsymlib/gsymlib.profile.svg

    .. rubric:: pstats Output

    .. literalinclude:: ../../../profiling/gedaif/gsymlib/gsymlib.profile.stats

    """
    pl = modules.get_prototype_lib(regen=False)
    for k, p in pl.iteritems():
        temp = p.validation_errors


def main():
    """
    The main function for this profiler module.
    """
    profilers = [generate_prototypelib,
                 generate_thick_prototypelib]
    for profiler in profilers:
        profiler()


if __name__ == '__main__':
    main()
