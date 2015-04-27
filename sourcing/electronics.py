"""
Electronics Sourcing module documentation (:mod:`sourcing.electronics`)
=======================================================================
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.DEBUG)

import vendors

import digikey
import csil

from entityhub import projects
import gedaif.gsymlib
import gedaif.conffile

import utils.currency
import utils.fs
import utils.config
from utils.progressbar.progressbar import ProgressBar

import entityhub.maps

import os
import csv


def gen_pcb_vendor_mapfile(vendor_obj):
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    if 'electronics_pcb' != vendor_obj.pclass:
        logger.warning('Vendor not an electronics vendor. Not generating eln map.')
        return None
    if 'electronics_pcb' == vendor_obj.pclass:
        logger.info('Generating PCB mapfile for ' + vendor_obj.name)

        pcblib = projects.pcbs
        pb = ProgressBar('red', block='#', empty='.')

        outp = vendor_obj.mappath
        outf = utils.fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Canonical', 'Strategy', 'Lparts'))

        nsymbols = len(pcblib)
        counter = 0

        for status in ['Active', 'Experimental', 'Deprecated']:
            for pcb, folder in pcblib.iteritems():
                conf = gedaif.conffile.ConfigsFile(folder)
                dstatus = conf.configdata['pcbdetails']['status']
                if dstatus == status:
                    vpnos, strategy = [[pcb], 'CUSTOM']
                    outw.writerow([pcb.strip(), strategy.strip()] + vpnos)
                    counter += 1
                    percentage = counter*100.00/nsymbols
                    pb.render(int(percentage), "\n%f%% %s\nGenerating Map File" % (percentage, pcb))
        outf.close()


def gen_vendor_mapfile(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    if 'electronics' != vendor_obj.pclass:
        logger.warning('Vendor not an electronics vendor. Not generating eln map.')
        return None
    if 'electronics' == vendor_obj.pclass:
        logger.info('Generating electronics mapfile for ' + vendor_obj.name)
        symlib = gedaif.gsymlib.gen_symlib()
        symlib.sort(key=lambda x: x.ident)
        pb = ProgressBar('red', block='#', empty='.')

        outp = vendor_obj.mappath
        outf = utils.fs.VersionedOutputFile(outp)
        outw = csv.writer(outf)
        outw.writerow(('Canonical', 'Strategy', 'Lparts'))

        nsymbols = len(symlib)
        counter = 0

        for status in ['Active', 'Experimental', 'Deprecated', 'Virtual', 'Generator']:
            for symbol in symlib:
                if symbol.status == status and symbol.ident.strip() != "":
                    vpnos, strategy = vendor_obj.search_vpnos(symbol.ident)
                    if vpnos is not None:
                        vpnos = [('@AG@' + vpno) for vpno in vpnos]
                    else:
                        # TODO Fix this error (hack around progressbar issue)
                        if strategy not in ['NODEVICE', 'NOVALUE']:
                            logger.warning("Could not find matches for : " + symbol.ident +
                                            '::' + str(strategy) +'\n\n\n')
                        vpnos = []
                    outw.writerow([symbol.ident.strip(), strategy.strip()] + vpnos)
                    counter += 1
                    percentage = counter*100.00/nsymbols
                    pb.render(int(percentage), "\n%f%% %s\nGenerating Map File" % (percentage, symbol.ident))
        outf.close()
    vendor_obj.map = vendor_obj.mappath

vendor_list = []


def init_vendors():
    global vendor_list
    for vendor in utils.config.VENDORS_DATA:
        logger.debug("Adding Vendor : " + vendor['name'])
        if 'electronics' in vendor['pclass']:
            vendor_obj = None
            mappath = vendor['mapfile-base'] + '-electronics.csv'
            # TODO Fix This.
            if vendor['name'] == 'digikey':
                vendor_obj = digikey.VendorDigiKey(vendor['name'],
                                                   vendor['dname'],
                                                   'electronics',
                                                   mappath,
                                                   'USD',
                                                   'US$'
                                                   )
                logger.debug("Created DK Vendor Object : " + vendor['name'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' + vendor['name'])
        if 'electronics_pcb' in vendor['pclass']:
            vendor_obj = None
            mappath = vendor['mapfile-base'] + '-electronics-pcb.csv'
            if vendor['name'] == 'csil':
                vendor_obj = csil.VendorCSIL(vendor['name'],
                                             vendor['dname'],
                                             'electronics_pcb',
                                             mappath,
                                             'INR',
                                             username=vendor['user'],
                                             password=vendor['pw']
                                             )
                logger.debug("Created CSIL Vendor Object : " + vendor['name'])
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logger.error('Vendor Handlers not found for vendor : ' + vendor['name'])


def export_vendor_map_audit(vendor_obj):
    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    mapobj = vendor_obj.map
    assert isinstance(mapobj, entityhub.maps.MapFile)

    outp = os.path.join(utils.config.vendor_map_audit_folder, vendor_obj.name + '-electronics-audit.csv')
    outf = utils.fs.VersionedOutputFile(outp)
    outw = csv.writer(outf)
    pb = ProgressBar('red', block='#', empty='.')
    idents = mapobj.get_idents()
    nidents = len(idents)
    idents.sort()
    for iidx, ident in enumerate(idents):
        nvpnos = len(idents)

        for pidx, vpno in enumerate(mapobj.get_all_partnos(ident)):
            vp = vendor_obj.get_vpart(vpno, ident)
            assert isinstance(vp, vendors.VendorElnPartBase)
            outw.writerow([vp.ident, vp.vpno, vp.mpartno, vp.package, vp.vpartdesc, vp.manufacturer, vp.vqtyavail, vp.abs_moq])
            percentage = (iidx + (1.00*pidx/nvpnos)) * 100.00 / nidents
            pb.render(int(percentage), "\n%f%% %s;%s\nGenerating Vendor Map Audit" % (percentage, ident, vpno))

    outf.close()

init_vendors()


class SourcingException(Exception):
    pass


def get_eff_acq_price(vsinfo):
    return vsinfo[2] * vsinfo[5].unit_price.native_value


def get_sourcing_information(ident, qty):
    # vobj, vpno, oqty, nbprice, ubprice, effprice
    sources = []

    for vendor in vendor_list:
        vsinfo = vendor.get_optimal_pricing(ident, qty)
        if vsinfo[1] is not None:
            sources.append(vsinfo)

    if len(sources) == 0:
        raise SourcingException

    selsource = sources[0]
    for vsinfo in sources:
        if get_eff_acq_price(vsinfo) < get_eff_acq_price(selsource):
            selsource = vsinfo
    return selsource
