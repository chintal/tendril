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
Docstring for map
"""

import os
import csv
import six
from future.utils import iteritems

from tendril.gedaif import gsymlib

from . import vendors
from .electronics import vendor_list

from .db import controller

from tendril.entityhub import projects
from tendril.utils.db import get_session
from tendril.utils import fsutils
from tendril.utils import config
from tendril.utils.terminal import TendrilProgressBar

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


def gen_mapfile(vendor, idents, maxage=-1):
    pb = TendrilProgressBar(max=len(idents))
    vendor_obj = controller.get_vendor(name=vendor.cname)
    for ident in idents:
        pb.next(note=ident)
        vpnos, strategy = vendor.search_vpnos(ident)
        if vpnos is not None:
            # pb.writeln("Found: {0}\n".format(ident))
            avpnos = vpnos
        else:
            if strategy not in ['NODEVICE', 'NOVALUE',
                                'NOT_IMPL']:
                pb.writeln("Not Found: {0:40}::{1}\n".format(ident, strategy))
            avpnos = []
        with get_session() as session:
            # pb.writeln("{0:25} {1}\n".format(ident, avpnos))
            controller.set_strategy(vendor=vendor_obj, ident=ident,
                                    strategy=strategy, session=session)
            controller.set_amap_vpnos(vendor=vendor_obj, ident=ident,
                                      vpnos=avpnos, session=session)
    pb.finish()
    vendor.map._dump_mapfile()


def gen_vendor_mapfile(vendor_obj, maxage=-1):
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

        gen_mapfile(vendor_obj, idents, maxage)
        logger.info("Done Generating Electronics Vendor Map : " +
                    vendor_obj.name)

    elif 'electronics_pcb' == vendor_obj.pclass:
        logger.info('Generating PCB mapfile for ' + vendor_obj.name)
        pcblib = projects.pcbs
        idents = []
        for pcb, folder in iteritems(pcblib):
            idents.append(pcb)

        gen_mapfile(vendor_obj, idents, maxage)
        logger.info("Done Generating PCB Vendor Map File : " + vendor_obj.name)
    else:
        logger.warning('Vendor pclass is not recognized. Not generating map.')
        return


def export_vendor_map_audit(vendor_obj, max_age=-1):
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
                vp = vendor_obj.get_vpart(vpno, ident, max_age)
            except vendors.VendorPartRetrievalError:
                logger.error(
                    "Permanent Retrieval Error while getting part {0} from "
                    "{1}. Removing from Map.".format(vpno, vendor_obj.name)
                )
                mapobj.remove_apartno(vpno, ident)
                continue
            except:
                logger.error("Unhandled Error while getting part {0} from {1}"
                             "".format(vpno, vendor_obj.name))
                raise
            if isinstance(vp, vendors.VendorElnPartBase):
                row = [vp.ident, vp.vpno, vp.mpartno, vp.package, vp.vpartdesc,
                       vp.manufacturer, vp.vqtyavail, vp.abs_moq]
            else:
                row = [vp.ident, vp.vpno, vp.mpartno, None, vp.vpartdesc,
                       vp.manufacturer, vp.vqtyavail, vp.abs_moq]

            outw.writerow([six.text_type(s).encode("utf-8") for s in row])

            pb.next(note=':'.join([ident, vpno]))
            # "\n%f%% %s;%s\nGenerating Vendor Map Audit" % (
            #         percentage, ident, vpno
    pb.finish()
    outf.close()
    logger.info("Written Vendor Map Audit to File : " + vendor_obj.name)
