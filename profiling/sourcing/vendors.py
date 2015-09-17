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
Docstring for digikey
"""

import shutil

from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput

from tendril.sourcing import electronics


def profile_vendor(vobj):
    with PyCallGraph(output=GraphvizOutput()):
        for ident in vobj.get_all_vparts():
            print ident

    shutil.move('pycallgraph.png', 'pycallgraph.{0}.png'.format(vobj._name))


def main():
    for vendor in electronics.vendor_list:
        profile_vendor(vendor)


if __name__ == '__main__':
    main()
