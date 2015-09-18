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
Docstring for vendors
"""

import cProfile
import pstats
import itertools
import os
import inspect
from subprocess import Popen, PIPE

from tendril.sourcing import electronics

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


def profile_vendor(vobj):
    for ident in itertools.islice(vobj.get_all_vparts(), 20):
        print ident


def main():
    for vendor in electronics.vendor_list:
        vname = vendor._name

        raw_fn = str('{0}.profile'.format(vname))
        stats_fn = str('{0}.profile.stats'.format(vname))
        svg_fn = str('{0}.profile.svg'.format(vname))

        cProfile.runctx('profile_vendor(vendor)',
                        globals(), locals(), filename=raw_fn)

        with open(stats_fn, 'w') as f:
            stats = pstats.Stats(raw_fn, stream=f)
            stats.strip_dirs().sort_stats('cumulative').print_stats()

        gprof_cmd = 'gprof2dot -f pstats {0}'.format(raw_fn).split(' ')
        dot_cmd = 'dot -Tsvg -o {0}'.format(svg_fn).split(' ')

        gprof_process = Popen(gprof_cmd, stdout=PIPE, cwd=SCRIPT_FOLDER)
        dot_process = Popen(dot_cmd, stdin=gprof_process.stdout, stdout=PIPE, cwd=SCRIPT_FOLDER)

        gprof_process.stdout.close()  # enable write error in dd if ssh dies
        out, err = dot_process.communicate()


if __name__ == '__main__':
    main()
