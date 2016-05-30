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

from tendril.sourcing.electronics import vendor_list
from tendril.sourcing import map

SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'genvmap'))
def profile_vendor_genvmap(vobj, name):
    """
    This function profiles vendor map file generation for the given vendor.
    This corresponds to the execution profile for searching for a part from
    the vendor.

    .. warning::
        Make sure that your cache already includes all the necessary files
        by first running the ``tendril-genvmaps`` script before running the
        profiler.

    """
    map.gen_vendor_mapfile(vobj)


@do_profile(os.path.join(SCRIPT_FOLDER, 'genvmapaudit'))
def profile_vendor_genvmapaudit(vobj, name):
    """
    This function profiles vendor map audit file generation for the given
    vendor. This no longer corresponds to the execution profile for
    retrieving a part from the vendor, since the data may be retrieved from
    the database.

    .. warning::
        Make sure that your cache already includes all the necessary files
        by first running the ``tendril-genvmapaudits`` script before running
        the profiler.

    """
    map.export_vendor_map_audit(vobj)


@do_profile(os.path.join(SCRIPT_FOLDER, 'get_part'))
def profile_vendor_get_part(vobj, name):
    """
    This function profiles :func:`tendril.sourcing.vendors.VendorBase.get_all_vparts`
    execution for the given vendor. Uses max_age=0 to avoid using the database cache.

    .. todo::
        Change this to only hit one part or so, to avoid API rate limit related
        issues.

    """
    for ident in vobj.get_all_vparts(max_age=0):
        print ident


@do_profile(os.path.join(SCRIPT_FOLDER, 'get_part_db'))
def profile_vendor_get_part_db(vobj, name):
    """
    This function profiles :func:`tendril.sourcing.vendors.VendorBase.get_all_vparts`
    execution for the given vendor. Uses the database cache, which would have been
    prepared by get_part by this stage.

    .. todo::
        Change this to only hit one part or so, to avoid API rate limit related
        issues.

    """
    for ident in vobj.get_all_vparts():
        print ident


def main():
    """
    The main function for this profiler module. Generates all three profiles
    for every configured vendor.

    .. toctree::

        profiling.sourcing.vendors.digikey
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
                 profile_vendor_get_part_db,
                 ]
    for vendor in vendor_list:
        for profiler in profilers:
            profiler(vendor, vendor._name)


if __name__ == '__main__':
    main()
