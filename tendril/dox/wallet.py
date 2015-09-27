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
Core Dox Wallet Module (:mod:`tendril.dox.wallet`)
==================================================

This module provides a simple wallet for 'standard' documents.
These documents would typically be stored within the
:data:`tendril.utils.config.DOCUMENT_WALLET_ROOT`, and defined by the
:data:`tendril.utils.config.DOCUMENT_WALLET` dictionary. Each `key, value`
pair in the dictionary is a `key, filename` pair.

This module is intended to be used by other ``tendril.dox`` modules to
provide document sets that include standard documents such as scanned IDs,
certificates, so on.

.. rubric:: Functions

.. autosummary::

    get_document_path
    is_in_wallet

"""

from fs.opener import fsopendir
from fs.utils import copyfile
from fs import path
from fs.errors import NoSysPathError

from tendril.utils.config import DOCUMENT_WALLET
from tendril.utils.config import DOCUMENT_WALLET_ROOT

from tendril.utils.fsutils import temp_fs


wallet_fs = fsopendir(DOCUMENT_WALLET_ROOT)
wallet_temp_fs = temp_fs.makeopendir('wallet')


def get_document_path(key):
    """
    Returns the absolute path to the document in the wallet referred to
    by the ``key``.

    If the wallet fs root is not an OS filesystem, then it copies the
    wallet document into the temporary folder and returns the path to it.

    :param key: Key of the document you want.
    :return: The absolute path to the document.
    """
    if key in DOCUMENT_WALLET.keys():
        try:
            return wallet_fs.getsyspath(DOCUMENT_WALLET[key])
        except NoSysPathError:
            if not wallet_temp_fs.exists(DOCUMENT_WALLET[key]):
                copyfile(wallet_fs, DOCUMENT_WALLET[key],
                         wallet_temp_fs, DOCUMENT_WALLET[key])
            return wallet_temp_fs.getsyspath(DOCUMENT_WALLET[key])
    else:
        raise ValueError


def is_in_wallet(fpath):
    """
    Checks whether a specified path points to a document in the wallet.
    This function only checks whether the path is within the
    :data:`tendril.utils.config.DOCUMENT_WALLET_ROOT`, and not whether the
    document is defined in the :data:`tendril.utils.config.DOCUMENT_WALLET`
    dictionary.

    The intended use of this function is alongside PDF merge operations
    after which the sources are deleted. Documents in the wallet should not
    be deleted. Code performing the deletion can use this function to check
    whether the document is in the wallet.

    :param fpath: The path to the file.
    :return: True if the document is in the wallet, False if not.

    """
    if DOCUMENT_WALLET_ROOT in path.split(fpath)[0]:
        return True
