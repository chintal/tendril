#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for expose
"""

import os
from fs.osfs import OSFS
from fs.utils import copyfile

from flask import Blueprint
from flask import send_file
from flask_user import login_required

from tendril.utils.config import DOCSTORE_ROOT
from tendril.utils.config import DOCSTORE_PREFIX
from tendril.utils.config import DOCUMENT_WALLET_ROOT
from tendril.utils.config import DOCUMENT_WALLET_PREFIX
from tendril.utils.config import REFDOC_ROOT
from tendril.utils.config import REFDOC_PREFIX

from tendril.utils.fsutils import temp_fs
from tendril.dox.docstore import refdoc_fs
from tendril.dox.docstore import docstore_fs
from tendril.dox.wallet import wallet_fs

expose = Blueprint('expose', __name__)
temp_expose_fs = temp_fs.makeopendir('expose')


def get_sendable_path(fspath, fs, fs_root):
    if isinstance(fs, OSFS):
        path = os.path.join(fs_root, fspath)
    else:
        path = temp_expose_fs.getsyspath(fspath)
        if not temp_expose_fs.exists(fspath):
            temp_expose_fs.makedir(
                os.path.split(fspath)[0],
                recursive=True,
                allow_recreate=True
            )
            copyfile(
                fs, fspath,
                temp_expose_fs, fspath
            )
    return path


@expose.route('/<path:path>')
@login_required
def static_proxy(path):
    fspath = path.split(os.path.sep, 1)[1]
    if path.startswith(DOCSTORE_PREFIX):
        path = get_sendable_path(fspath, docstore_fs, DOCSTORE_ROOT)
    elif path.startswith(DOCUMENT_WALLET_PREFIX):
        path = get_sendable_path(fspath, wallet_fs, DOCUMENT_WALLET_ROOT)
    elif path.startswith(REFDOC_PREFIX):
        path = get_sendable_path(fspath, refdoc_fs, REFDOC_ROOT)
    else:
        raise IOError('Unknown expose file : ' + path)
    if not os.path.exists(path):
        raise IOError('Expose file does not exist : ' + path)
    return send_file(path)
