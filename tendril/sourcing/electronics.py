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

import vendors
import orders

import digikey
import mouser
import ti
import csil
import pricelist

from db import controller

from tendril.entityhub import projects
from tendril.gedaif import gsymlib

from tendril.utils.db import get_session
from tendril.utils import fsutils
from tendril.utils import config
from tendril.utils.terminal import TendrilProgressBar

import os
import csv

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


def gen_mapfile(vendor, idents):
    pb = TendrilProgressBar(max=len(idents))
    vendor_obj = controller.get_vendor(name=vendor._name)
    for ident in idents:
        pb.next(note=ident)
        vpnos, strategy = vendor.search_vpnos(ident)
        if vpnos is not None:
            pb.writeln("Found: {0}".format(ident))
            avpnos = vpnos
        else:
            if strategy not in ['NODEVICE', 'NOVALUE',
                                'NOT_IMPL']:
                pb.writeln("Not Found: {0}::{1}\n".format(ident, strategy))
            avpnos = []
        with get_session() as session:
            controller.set_strategy(vendor=vendor_obj, ident=ident,
                                    strategy=strategy, session=session)
            controller.set_amap_vpnos(vendor=vendor_obj, ident=ident,
                                      vpnos=avpnos, session=session)
    pb.finish()


def gen_vendor_mapfile(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]

    if 'electronics' == vendor_obj.pclass:
        logger.info('Generating electronics mapfile for ' + vendor_obj.name)
        symlib = gsymlib.gen_symlib()
        symlib.sort(key=lambda x: x.ident)

        idents = []

        for symbol in symlib:
            if symbol.ident.strip() != "":
                idents.append(symbol.ident)

        gen_mapfile(vendor_obj, idents)
        logger.info("Done Generating Electronics Vendor Map : " +
                    vendor_obj.name)

    elif 'electronics_pcb' == vendor_obj.pclass:
        logger.info('Generating PCB mapfile for ' + vendor_obj.name)
        pcblib = projects.pcbs
        idents = []
        for pcb, folder in pcblib.iteritems():
            idents.append(pcb)

        gen_mapfile(vendor_obj, idents)
        logger.info("Done Generating PCB Vendor Map File : " + vendor_obj.name)
    else:
        logger.warning('Vendor pclass is not recognized. Not generating map.')
        return

vendor_list = []


def init_vendors():
    global vendor_list
    for vendor in config.VENDORS_DATA:
        logger.debug("Adding Vendor : " + vendor['name'])
        if 'electronics' in vendor['pclass']:
            vendor_obj = None
            # TODO Fix This.
            if vendor['name'] == 'digikey':
                vendor_obj = digikey.VendorDigiKey(vendor['name'],
                                                   vendor['dname'],
                                                   'electronics',
                                                   currency_code='USD',
                                                   currency_symbol='US$'
                                                   )
                logger.info("Created DK Vendor Object : " + vendor['dname'])
            if vendor['name'] == 'mouser':
                vendor_obj = mouser.VendorMouser(vendor['name'],
                                                 vendor['dname'],
                                                 'electronics',
                                                 currency_code='USD',
                                                 currency_symbol='US$'
                                                 )
                logger.info("Created Mouser Vendor Object : " +
                            vendor['dname'])
            if vendor['name'] == 'ti':
                vendor_obj = ti.VendorTI(vendor['name'],
                                         vendor['dname'],
                                         'electronics',
                                         currency_code='USD',
                                         currency_symbol='US$'
                                         )
                logger.info("Created TI Vendor Object : " + vendor['dname'])
            if vendor['type'] == 'pricelist':
                vendor_obj = pricelist.VendorPricelist(vendor['name'],
                                                       vendor['dname'],
                                                       'electronics')
                logger.info("Created Pricelist Vendor Object : " +
                            vendor['dname'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' +
                             vendor['name'])
        if 'electronics_pcb' in vendor['pclass']:
            vendor_obj = None
            if vendor['name'] == 'csil':
                vendor_obj = csil.VendorCSIL(vendor['name'],
                                             vendor['dname'],
                                             'electronics_pcb',
                                             currency_code='INR',
                                             username=vendor['user'],
                                             password=vendor['pw']
                                             )
                logger.info("Created CSIL Vendor Object : " + vendor['dname'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' +
                             vendor['name'])


def export_vendor_map_audit(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    mapobj = vendor_obj.map
    outp = os.path.join(config.VENDOR_MAP_AUDIT_FOLDER,
                        vendor_obj.name + '-electronics-audit.csv')
    outf = fsutils.VersionedOutputFile(outp)
    outw = csv.writer(outf)
    total = mapobj.length()
    pb = TendrilProgressBar(max=total)
    for ident in mapobj.get_idents():
        for vpno in mapobj.get_all_partnos(ident):
            try:
                vp = vendor_obj.get_vpart(vpno, ident)
            except:
                logger.error("Error while getting part {0} from {1}".format(
                    vpno, vendor_obj.name
                ))
                raise
            try:
                assert isinstance(vp, vendors.VendorElnPartBase)
                outw.writerow([vp.ident, vp.vpno, vp.mpartno, vp.package,
                               vp.vpartdesc, vp.manufacturer,
                               vp.vqtyavail, vp.abs_moq])
            except AssertionError:
                outw.writerow([vp.ident, vp.vpno, vp.mpartno, None,
                               vp.vpartdesc, vp.manufacturer,
                               vp.vqtyavail, vp.abs_moq])

            pb.next(note=':'.join([ident, vpno]))
            # "\n%f%% %s;%s\nGenerating Vendor Map Audit" % (
            #         percentage, ident, vpno
    pb.finish()
    outf.close()
    logger.info("Written Vendor Map Audit to File : " + vendor_obj.name)

init_vendors()


class SourcingException(Exception):
    pass


def get_eff_acq_price(vsinfo, qty):
    return vsinfo[2] * vsinfo[5].unit_price.native_value


def get_sourcing_information(ident, qty, avendors=vendor_list,
                             allvendors=False):
    # vobj, vpno, oqty, nbprice, ubprice, effprice
    sources = []
    ident = ident.strip()
    for vendor in avendors:
        vsinfo = vendor.get_optimal_pricing(ident, qty)
        if vsinfo[1] is not None:
            sources.append(vsinfo)

    if len(sources) == 0:
        raise SourcingException

    if allvendors is False:
        selsource = sources[0]
        for vsinfo in sources:
            if get_eff_acq_price(vsinfo, qty) < get_eff_acq_price(selsource, qty):  # noqa
                selsource = vsinfo
        return selsource
    else:
        return sources

order = orders.CompositeOrder(vendor_list)


# def get_vendor_by_name(name):
#     for vendor in vendor_list:
#         if vendor.vendor_name == name:
#             return vendor
#     return None


def get_vendor_by_name(name):
    for vendor in vendor_list:
        if vendor._name == name:
            return vendor
    return None
