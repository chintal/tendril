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
Docstring for profiler.py
"""

import os
import functools
import cProfile
import pstats
from subprocess import Popen, PIPE


def do_profile(folder, name=None):
    def wrap(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if name:
                lname = name
            else:
                lname = args[-1]

            if not os.path.exists(folder):
                os.makedirs(folder)

            raw_fn = str('{0}.profile'.format(lname))
            raw_fn = os.path.join(folder, raw_fn)
            stats_fn = str('{0}.profile.stats'.format(lname))
            stats_fn = os.path.join(folder, stats_fn)
            svg_fn = str('{0}.profile.svg'.format(lname))
            svg_fn = os.path.join(folder, svg_fn)

            profile = cProfile.Profile()
            try:
                profile.enable()
                result = func(*args, **kwargs)
                profile.disable()
            finally:
                profile.dump_stats(raw_fn)

            with open(stats_fn, 'w') as f:
                stats = pstats.Stats(raw_fn, stream=f)
                stats.strip_dirs().sort_stats('cumulative').print_stats()

            gprof_cmd = 'gprof2dot -f pstats {0}'.format(raw_fn).split(' ')
            dot_cmd = 'dot -Tsvg -o {0}'.format(svg_fn).split(' ')

            gprof_process = Popen(gprof_cmd, stdout=PIPE, cwd=folder)
            dot_process = Popen(dot_cmd, stdin=gprof_process.stdout, stdout=PIPE, cwd=folder)

            gprof_process.stdout.close()
            dot_process.communicate()
            return result
        return inner
    return wrap
