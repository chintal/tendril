"""
Config Module Documentation (:mod:`utils.config`)
=================================================
"""

import os
import inspect

CONFIG_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
KOALA_ROOT = os.path.normpath(os.path.join(CONFIG_PATH, os.pardir, os.pardir))
AUDIT_PATH = os.path.join(KOALA_ROOT, 'manual-audit')
# Network Details

NETWORK_PROXY_TYPE = 'http'
NETWORK_PROXY_IP = '192.168.1.254'
NETWORK_PROXY_PORT = '3128'
# NETWORK_PROXY_IP = 'localhost'
# NETWORK_PROXY_PORT = '8080'
NETWORK_PROXY_USER = 'chintal'
NETWORK_PROXY_PASS = 'chintal'
ENABLE_REDIRECT_CACHING = True

# Currency Details
BASE_CURRENCY = 'INR'
BASE_CURRENCY_SYMBOL = 'INR '

# Company Details

COMPANY_LOGO_PATH = os.path.join(KOALA_ROOT, 'dox/templates/graphics/logo.png')
COMPANY_NAME = "Quazar Technologies Pvt Ltd"

DOX_TEMPLATE_FOLDER = os.path.join(KOALA_ROOT, 'dox/templates')


# gEDA Details

GEDA_SCHEME_DIR = "/usr/share/gEDA/scheme"
GAF_ROOT = os.path.join(os.path.expanduser('~'), 'gEDA2')
GEDA_SYMLIB_ROOT = os.path.join(GAF_ROOT, 'symbols')


# Inventory Details

_svn_stock_folder = '/home/chintal/quazar/svn/Stock/QUAZAR/ESTORE/'
_svn_current_estore_xls_file = 'estore2014-2015.xls'

ELECTRONICS_INVENTORY_DATA = [
    {
        'fpath': os.path.join(_svn_stock_folder, _svn_current_estore_xls_file),
        'sname': 'ElectronicsLive',
        'location': 'Main Electronics Production Stock',
        'type': 'QuazarStockXLS',
        'tfpath': os.path.join(KOALA_ROOT, 'inventory/transforms', 'ElectronicsLive-tf.csv')
    },

    {
        'fpath': os.path.join(_svn_stock_folder, _svn_current_estore_xls_file),
        'sname': 'ElectricalLive',
        'location': 'Main Electrical Production Stock',
        'type': 'QuazarStockXLS',
        'tfpath': os.path.join(KOALA_ROOT, 'inventory/transforms', 'ElectricalLive-tf.csv')
    },

    {
        'fpath': os.path.join(_svn_stock_folder, 'QDA_Stock.xls'),
        'sname': 'Sheet1',
        'location': 'QDA Electronics Stock',
        'type': 'QuazarStockXLS',
        'tfpath': os.path.join(KOALA_ROOT, 'inventory/transforms', 'QDA_Stock-tf.csv')
    },
]


# Vendor Details

_vendor_map_folder = os.path.join(KOALA_ROOT, 'sourcing/maps')
vendor_map_audit_folder = os.path.join(KOALA_ROOT, 'manual-audit', 'vendor-maps')

VENDORS_DATA = [
    {
        'name': 'digikey',
        'dname': 'Digi-Key Corporation',
        'mapfile-base': os.path.join(_vendor_map_folder, 'digikey'),
        'pclass': ['electronics']
    }
]
