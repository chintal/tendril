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
Docstring for views
"""

from flask import render_template
from flask_user import login_required

from . import invtransforms as blueprint

from tendril.inventory import electronics as invelectronics
from tendril.utils.fsutils import Crumb
from tendril.gedaif import gsymlib


@blueprint.route('/<location_idx>')
@blueprint.route('/')
@login_required
def transforms(location_idx=None):
    if location_idx is None:
        locs = invelectronics.inventory_locations
        idents = gsymlib.gsymlib_idents
        stage = {'idents': idents,
                 'locs': locs,
                 'crumbroot': '/inventory',
                 'inv': invelectronics,
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Transforms", path="transform/")],
                 }
        return render_template('overview.html', stage=stage,
                               pagetitle="All Inventory Transforms")
    else:
        loc = invelectronics.inventory_locations[int(location_idx)]
        stage = {'loc': loc,
                 'tf': loc.tf,
                 'gsymlib_idents': gsymlib.gsymlib_idents,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Transforms", path="transform/"),
                                 Crumb(name=loc.name, path="transform/" + location_idx)],  # noqa
                 }
        return render_template('transform_detail.html', stage=stage,
                               pagetitle="Inventory Transform " + loc.name)
