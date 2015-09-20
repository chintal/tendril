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
from flask_user import login_required

from tendril.utils.config import INSTANCE_ROOT


expose = Blueprint('expose', __name__,
                   static_folder=os.path.join(INSTANCE_ROOT, 'mp_exposed'))


@expose.route('/<path:path>')
@login_required
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return expose.send_static_file(path)
