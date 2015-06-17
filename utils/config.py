"""
Config Module Documentation (:mod:`utils.config`)
=================================================
"""

import os
import inspect
import imp


CONFIG_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
KOALA_ROOT = os.path.normpath(os.path.join(CONFIG_PATH, os.pardir, os.pardir))
INSTANCE_ROOT = os.path.join(os.path.expanduser('~'), '.koala')
INSTANCE_CONFIG_FILE = os.path.join(INSTANCE_ROOT, 'instance_config.py')
DOX_TEMPLATE_FOLDER = os.path.join(KOALA_ROOT, 'dox/templates')


def import_(filename):
    (path, name) = os.path.split(filename)
    (name, ext) = os.path.splitext(name)

    (f, filename, data) = imp.find_module(name, [path])
    return imp.load_module(name, f, filename, data)

INSTANCE_CONFIG = import_(INSTANCE_CONFIG_FILE)

AUDIT_PATH = INSTANCE_CONFIG.AUDIT_PATH
PROJECTS_ROOT = INSTANCE_CONFIG.PROJECTS_ROOT
SVN_ROOT = INSTANCE_CONFIG.SVN_ROOT
INSTANCE_CACHE = INSTANCE_CONFIG.INSTANCE_CACHE

# gEDA Configuration
GEDA_SCHEME_DIR = INSTANCE_CONFIG.GEDA_SCHEME_DIR
GAF_ROOT = INSTANCE_CONFIG.GAF_ROOT
GEDA_SYMLIB_ROOT = INSTANCE_CONFIG.GEDA_SYMLIB_ROOT

# Network Configuration
NETWORK_PROXY_TYPE = INSTANCE_CONFIG.NETWORK_PROXY_TYPE
NETWORK_PROXY_IP = INSTANCE_CONFIG.NETWORK_PROXY_IP
NETWORK_PROXY_PORT = INSTANCE_CONFIG.NETWORK_PROXY_PORT
NETWORK_PROXY_USER = INSTANCE_CONFIG.NETWORK_PROXY_USER
NETWORK_PROXY_PASS = INSTANCE_CONFIG.NETWORK_PROXY_PASS
ENABLE_REDIRECT_CACHING = INSTANCE_CONFIG.ENABLE_REDIRECT_CACHING

TRY_REPLICATOR_CACHE_FIRST = INSTANCE_CONFIG.TRY_REPLICATOR_CACHE_FIRST
REPLICATOR_PROXY_TYPE = INSTANCE_CONFIG.REPLICATOR_PROXY_TYPE
REPLICATOR_PROXY_IP = INSTANCE_CONFIG.REPLICATOR_PROXY_IP
REPLICATOR_PROXY_PORT = INSTANCE_CONFIG.REPLICATOR_PROXY_PORT
REPLICATOR_PROXY_USER = INSTANCE_CONFIG.REPLICATOR_PROXY_USER
REPLICATOR_PROXY_PASS = INSTANCE_CONFIG.REPLICATOR_PROXY_PASS

# Currency Configuration
BASE_CURRENCY = INSTANCE_CONFIG.BASE_CURRENCY
BASE_CURRENCY_SYMBOL = INSTANCE_CONFIG.BASE_CURRENCY_SYMBOL

# Company Configuration
COMPANY_LOGO_PATH = INSTANCE_CONFIG.COMPANY_LOGO_PATH
COMPANY_PO_LCO_PATH = INSTANCE_CONFIG.COMPANY_PO_LCO_PATH
COMPANY_PO_POINT = INSTANCE_CONFIG.COMPANY_PO_POINT
COMPANY_NAME = INSTANCE_CONFIG.COMPANY_NAME

# Inventory Details
ELECTRONICS_INVENTORY_DATA = INSTANCE_CONFIG.ELECTRONICS_INVENTORY_DATA

# Vendor Details
vendor_map_audit_folder = INSTANCE_CONFIG.vendor_map_audit_folder
PRICELISTVENDORS_FOLDER = INSTANCE_CONFIG.PRICELISTVENDORS_FOLDER
VENDORS_DATA = INSTANCE_CONFIG.VENDORS_DATA
