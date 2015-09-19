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
sourcing.vendors Profiling
--------------------------

This file generates execution profiles for :mod:`tendril.sourcing.vendors`
and subclasses thereof.
"""


import os
import inspect

from ..profiler import do_profile

from tendril.sourcing import electronics

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'genvmap'))
def profile_vendor_genvmap(vobj, name):
    """
    This function profiles vendor map file generation for the given vendor.
    This corresponds to the execution profile for searching for a part from
    the vendor.

    """
    electronics.gen_vendor_mapfile(vobj)


@do_profile(os.path.join(SCRIPT_FOLDER, 'genvmapaudit'))
def profile_vendor_genvmapaudit(vobj, name):
    """
    This function profiles vendor map audit file generation for the given vendor.
    This corresponds to the execution profile for retrieving a part from the
    vendor.

    """
    electronics.export_vendor_map_audit(vobj)


@do_profile(os.path.join(SCRIPT_FOLDER, 'get_part'))
def profile_vendor_get_part(vobj, name):
    """
    This function profiles :func:`tendril.sourcing.vendors.VendorBase.get_all_vparts`
    execution for the given vendor.

    """
    for ident in vobj.get_all_vparts():
        print ident


def main():
    """
    The main function for this profiler module. Generates all three profiles
    for every configured vendor.

    .. toctree::

        profiling.sourcing.vendors.digikey
        profiling.sourcing.vendors.mouser
        profiling.sourcing.vendors.ti
        profiling.sourcing.vendors.csil
        profiling.sourcing.vendors.pricelist

    """
    # TODO
    # Maybe set this up to invalidate caches first,
    # and run profiling with and without caches.

    # TODO
    # Record total runtime and such, perhaps?

    profilers = [profile_vendor_genvmap,
                 profile_vendor_genvmapaudit,
                 profile_vendor_get_part,
                 ]
    for vendor in electronics.vendor_list:
        for profiler in profilers:
            profiler(vendor, vendor._name)


if __name__ == '__main__':
    main()
