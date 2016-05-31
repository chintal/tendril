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
entityhub.modules Profiling
---------------------------

This file runs profiling on :mod:`tendril.gedaif.gsymlib`.
"""

import os
import timeit
import inspect

from ..profiler import do_profile

from tendril.entityhub import modules

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'modules'), 'modules')
def generate_prototypelib():
    """
    Profiles the prototype library generation.

    When the ``entityhub.modules`` module is loaded, it automatically generates the
    prototype library from the projects on the filesystem. This function profiles
    the generation of the (thin) library.

    :download:`Raw execution profile <../../../profiling/entityhub/modules/modules.profile>`
    :download:`SVG of execution profile <../../../profiling/entityhub/modules/modules.profile.svg>`

    .. rubric:: Execution Profile

    .. image:: ../../../profiling/entityhub/modules/modules.profile.svg

    .. rubric:: pstats Output

    .. literalinclude:: ../../../profiling/entityhub/modules/modules.profile.stats

    """
    return modules.get_prototype_lib(regen=True)


@do_profile(os.path.join(SCRIPT_FOLDER, 'modules'), 'modules_thick')
def generate_thick_prototypelib():
    """
    Profiles the prototype library generation with full object instantiation.

    The prototypes created at module load are thin prototypes, with various
    sections left for on-demand loading by default. This is useful when
    tendril is used as a script. However, when run as a server, this filling
    out of each prototype makes the first page load (per daemon) an
    incredibly slow process.

    This function prototypes the validation of each prototype. The validation
    process necessarily requires thick prototypes, since much of the data to be
    validated resides in the information not loaded on object instantiation.
    Tendril also uses the same validation hook to warm up it's caches when
    run as a server (as controlled by the WARM_UP_CACHES config option).

    :download:`Raw execution profile <../../../profiling/entityhub/modules/modules_thick.profile>`
    :download:`SVG of execution profile <../../../profiling/entityhub/modules/modules_thick.profile.svg>`

    .. rubric:: Execution Profile

    .. image:: ../../../profiling/entityhub/modules/modules_thick.profile.svg

    .. rubric:: pstats Output

    .. literalinclude:: ../../../profiling/entityhub/modules/modules_thick.profile.stats

    """
    pl = modules.get_prototype_lib(regen=False)
    tcount = len(pl.keys())
    count = 0
    for k, p in pl.iteritems():
        count += 1
        start_time = timeit.default_timer()
        temp = p.validation_errors
        elapsed = timeit.default_timer() - start_time
        print "{2:>3}/{3:3} Filled out {0:40} took {1:>6.2f}s" \
              "".format(k, elapsed, count, tcount)


# @do_profile(os.path.join(SCRIPT_FOLDER, 'modules'), 'modules_costing')
# def generate_costing():
#     p = modules.get_module_prototype('QM-DA14-81A-2M2-R1')
#     obom = p.obom
#     print obom.indicative_cost


def main():
    """
    The main function for this profiler module.
    """
    profilers = [generate_prototypelib,
                 generate_thick_prototypelib,]
    for profiler in profilers:
        profiler()


if __name__ == '__main__':
    main()
