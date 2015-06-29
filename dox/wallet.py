"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os

from utils.config import DOCUMENT_WALLET
from utils.config import DOCUMENT_WALLET_ROOT

def get_document_path(key):
    if key in DOCUMENT_WALLET.keys():
        return os.path.join(DOCUMENT_WALLET_ROOT, DOCUMENT_WALLET[key])
    else:
        raise ValueError

def is_in_wallet(fpath):
    if DOCUMENT_WALLET_ROOT in os.path.split(fpath)[0]:
        return True
