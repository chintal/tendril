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

from collections import namedtuple
from future.utils import viewitems
from tendril.boms.outputbase import CompositeOutputBom
from tendril.entityhub.modules import get_prototype_lib
from tendril.utils.config import WARM_UP_CACHES
from tendril.utils import log

logger = log.get_logger(__name__, log.DEFAULT)


context_cardlisting = namedtuple(
    'ContextCardListing',
    'name, desc, status, qty, proj, projdesc, projstatus'
)
simple_cardlisting = namedtuple(
    'SimpleCardListing',
    'name, desc, status, qty'
)


def _status_filter(cards, diversity=8):
    if not diversity:
        return cards
    if not cards:
        return cards
    used_statuses = []
    for card in cards:
        if card.status not in used_statuses:
            used_statuses.append(card.status)
    used_statuses.sort()
    if len(used_statuses) > diversity:
        allowed_statuses = used_statuses[:diversity]
    else:
        allowed_statuses = used_statuses
    return [x for x in cards if x.status in allowed_statuses]


def _group_by_pcbname(cards):
    rval = {}
    if not cards:
        return {}
    for card in cards:
        ncard = simple_cardlisting(card.name, card.desc,
                                   card.status, card.qty)
        if card.proj in rval.keys():
            rval[card.proj][1].append(ncard)
        else:
            rval[card.proj] = [card.projdesc, [ncard],
                               card.projstatus, None, None]
    for key, value in viewitems(rval):
        qtys = [x.qty for x in value[1]]
        value[3] = min(qtys)
        value[4] = max(qtys)
        if value[3] == value[4]:
            value[4] = None
        value[1] = sorted(value[1], key=lambda y: y.name)
    return rval


def get_symbol_inclusion(ident):
    cobom = get_bom_superset()
    line = cobom.find_by_ident(ident)
    cards = None
    if line:
        cards = []
        for idx, column in enumerate(line.columns):
            if column > 0:
                cardname = cobom.descriptors[idx].configname
                configs = cobom.descriptors[idx].configurations
                carddesc = configs.description(cardname)
                pcbstatus = configs.status_config(cardname)
                proj = configs.pcbname
                projdesc = configs.description()
                projstatus = configs.status
                cards.append(context_cardlisting(
                    cardname, carddesc, pcbstatus, column,
                    proj, projdesc, projstatus))
    return _group_by_pcbname(_status_filter(cards))


superset_cobom = None


def get_bom_superset(regen=False):
    global superset_cobom
    if not regen and superset_cobom is not None:
        return superset_cobom
    prototypes = get_prototype_lib()
    boms = []
    logger.info("Building superset composite BOM")
    for ident, prototype in viewitems(prototypes):
        boms.append(prototype.obom)
    logger.info("Collating into superset composite BOM")
    superset_cobom = CompositeOutputBom(boms, name='ALL')
    superset_cobom.collapse_wires()
    return superset_cobom

if WARM_UP_CACHES is True:
    get_bom_superset()
