# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
Electronics Sourcing module documentation (:mod:`sourcing.electronics`)
=======================================================================
"""

import copy
import importlib

from tendril.utils import config
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


def init_vendors():
    vlist = []
    vdatalist = copy.copy(config.VENDORS_DATA)
    for vendor in vdatalist:
        vtype = vendor.get('vtype', None)
        if not vtype:
            logger.error('Vendor Type not defined for {0}'
                         ''.format(vendor['name']))
            continue
        module_name = '.{0}'.format(vtype.lower())
        module = importlib.import_module(module_name, __package__)
        class_name = 'Vendor{0}'.format(vtype)
        cls = getattr(module, class_name)
        logger.info("Adding Vendor : {0}".format(vendor['dname']))
        vendor_obj = cls(**vendor)
        if vendor_obj:
            vlist.append(vendor_obj)
        else:
            logger.error('Vendor Handlers not found for vendor : ' +
                         vendor['name'])
    return vlist


class SourcingException(Exception):
    pass


vendor_list = init_vendors()


def get_eff_acq_price(vsinfo):
    return vsinfo.oqty * vsinfo.effprice.unit_price.native_value


def get_sourcing_information(ident, qty, avendors=vendor_list,
                             allvendors=False, get_all=False):
    sources = []
    ident = ident.strip()

    if ident.startswith('PCB'):
        pclass = 'electronics_pcb'
    else:
        pclass = 'electronics'

    for vendor in avendors:
        if vendor.pclass == pclass:
            vsinfo = vendor.get_optimal_pricing(ident, qty, get_all=get_all)
            if not get_all:
                if vsinfo.vpart is not None:
                    sources.append(vsinfo)
            else:
                sources.extend(vsinfo)
    if len(sources) == 0:
        raise SourcingException
    if get_all is False and allvendors is False:
        selsource = sources[0]
        for vsinfo in sources:
            if get_eff_acq_price(vsinfo) < get_eff_acq_price(selsource):
                selsource = vsinfo
        return selsource
    else:
        return sorted(sources, key=lambda x: get_eff_acq_price(x))


def get_vendor_by_name(name):
    for vendor in vendor_list:
        if vendor._name == name:
            return vendor
    return None
