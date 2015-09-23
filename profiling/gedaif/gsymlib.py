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
gedaif.gsymlib Profiling
------------------------

This file runs profiling on :mod:`tendril.gedaif.gsymlib`.
"""

import os
import inspect

from ..profiler import do_profile

from tendril.gedaif import gsymlib

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'gsymlib'), 'gsymlib')
def generate_gsymlib():
    """
    Profiles gsymlib generation.

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
    symlib = gsymlib.gen_symlib()


def main():
    """
    The main function for this profiler module.
    """

    # TODO
    # Maybe set this up to invalidate caches first,
    # and run profiling with and without caches.

    # TODO
    # Record total runtime and such, perhaps?

    profilers = [generate_gsymlib]
    for profiler in profilers:
        profiler()


if __name__ == '__main__':
    main()
