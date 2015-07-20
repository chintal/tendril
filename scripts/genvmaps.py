"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import sourcing.electronics


for vendor in sourcing.electronics.vendor_list:
    sourcing.electronics.gen_vendor_mapfile(vendor)
