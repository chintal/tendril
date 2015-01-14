"""
Electronics Sourcing module documentation (:mod:`sourcing.electronics`)
=======================================================================
"""

import vendors
import digikey

import gedaif.gsymlib
import utils.currency
import utils.fs
import utils.config
from utils.progressbar.progressbar import ProgressBar

import entityhub.maps

import os
import csv
import logging


def gen_vendor_mapfile(vendor_obj):

    """

    :type vendor_obj: sourcing.vendors.VendorBase
    """
    if isinstance(vendor_obj, int):
        vendor_obj = vendor_list[vendor_obj]
    if 'electronics' not in vendor_obj.pclass:
        logging.warning('Vendor not an electronics vendor. Not generating map.')
        return None

    logging.info('Generating electronics mapfile for ' + vendor_obj.name)
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
                        logging.warning("Could not find matches for : " + symbol.ident +
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
            if vendor_obj:
                vendor_list.append(vendor_obj)
            else:
                logging.error('Vendor Handlers not found for vendor : ' + vendor['name'])


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
