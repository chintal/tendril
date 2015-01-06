"""
Electronics Sourcing module documentation (:mod:`sourcing.electronics`)
=======================================================================
"""

import gedaif.gsymlib
import utils.fsutils
import utils.config

import csv
import logging


def gen_vendor_mapfile(config_vendor_data_idx):
    vdata = utils.config.VENDORS_DATA[config_vendor_data_idx]
    if 'electronics' not in vdata["pclass"]:
        logging.warning('Vendor not an electronics vendor. Not generating map.')
        return None

    mappath = vdata['mapfile-base'] + 'electronics.csv'
    symlib = gedaif.gsymlib.gen_symlib()

    outp = mappath
    outf = utils.fsutils.VersionedOutputFile(outp)
    outw = csv.writer(outf)
    outw.writerow(('Canonical', 'DKparts'))
    for symbol in symlib:
        if symbol.ident.strip() != "":
            outw.writerow((symbol.ident.strip(), ' '))
    outf.close()
