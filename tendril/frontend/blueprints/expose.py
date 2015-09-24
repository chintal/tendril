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

from flask import Blueprint
from flask import send_file
from flask_user import login_required

from tendril.utils.config import DOCSTORE_ROOT
from tendril.utils.config import DOCSTORE_PREFIX
from tendril.utils.config import DOCUMENT_WALLET_ROOT
from tendril.utils.config import DOCUMENT_WALLET_PREFIX
from tendril.utils.config import REFDOC_ROOT
from tendril.utils.config import REFDOC_PREFIX

expose = Blueprint('expose', __name__)


@expose.route('/<path:path>')
@login_required
def static_proxy(path):
    if path.startswith(DOCSTORE_PREFIX):
        path = os.path.join(DOCSTORE_ROOT, path.split(os.path.sep, 1)[1])
    elif path.startswith(DOCUMENT_WALLET_PREFIX):
        path = os.path.join(DOCUMENT_WALLET_ROOT, path.split(os.path.sep, 1)[1])  # noqa
    elif path.startswith(REFDOC_PREFIX):
        path = os.path.join(REFDOC_ROOT, path.split(os.path.sep, 1)[1])
    else:
        raise IOError('Unknown expose file : ' + path)
    if not os.path.exists(path):
        raise IOError('Expose file does not exist : ' + path)
    return send_file(path)
