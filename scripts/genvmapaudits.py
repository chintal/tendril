"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import sourcing.electronics


for vendor in sourcing.electronics.vendor_list:
    sourcing.electronics.export_vendor_map_audit(vendor)
