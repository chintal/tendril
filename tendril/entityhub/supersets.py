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
Docstring for supersets.py
"""

from tendril.boms.outputbase import CompositeOutputBom
from tendril.entityhub.modules import prototypes
from tendril.utils import log

logger = log.get_logger(__name__, log.DEFAULT)


superset_cobom = None


def get_bom_superset(regen=False):
    global superset_cobom
    if not regen and superset_cobom is not None:
        return superset_cobom
    boms = []
    logger.info("Building superset composite BOM")
    for ident, prototype in prototypes.iteritems():
        boms.append(prototype.obom)
    logger.info("Collating into superset composite BOM")
    superset_cobom = CompositeOutputBom(boms, name='ALL')
    superset_cobom.collapse_wires()
    return superset_cobom
