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

import os
import inspect

from ..profiler import do_profile

from tendril.sourcing import electronics

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile
def profile_vendor_get_part(vobj):
    for ident in vobj.get_all_vparts():
        print ident


@do_profile
def profile_vendor_genvmap(vobj):
    electronics.gen_vendor_mapfile(vobj)


@do_profile
def profile_vendor_genvmapaudit(vobj):
    electronics.export_vendor_map_audit(vobj)


def main():

    # TODO
    # Maybe set this up to invalidate caches first,
    # and run profiling with and without caches.

    # TODO
    # Record total runtime and such, perhaps?

    profilers = [('get_part', profile_vendor_get_part),
                 ('genvmap', profile_vendor_genvmap),
                 ('genvmapaudit', profile_vendor_genvmapaudit),
                 ]
    for vendor in electronics.vendor_list:
        for profiler in profilers:
            folder = os.path.join(SCRIPT_FOLDER, profiler[0])
            profiler[1](vendor._name, folder, vobj=vendor)


if __name__ == '__main__':
    main()
