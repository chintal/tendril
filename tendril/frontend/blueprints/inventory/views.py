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

from . import inventory as blueprint

from tendril.inventory import electronics as invelectronics
from tendril.utils.fsutils import Crumb


@blueprint.route('/<location_idx>')
@blueprint.route('/')
@login_required
def status(location_idx=None):
    # Presently only supports getting the latest result. A way to allow
    # any result to be retrieved would be nice.
    if location_idx is None:
        locs = invelectronics.inventory_locations
        idents = []
        for loc in locs:
            for line in loc.lines:
                if line.ident not in idents:
                    idents.append(line.ident)
        stage = {'idents': idents,
                 'locs': locs,
                 'crumbroot': '/inventory',
                 'inv': invelectronics,
                 'breadcrumbs': [Crumb(name="Inventory", path="/"),
                                 Crumb(name="Status", path="location/")],
                 }
        return render_template('status.html', stage=stage,
                               pagetitle="All Inventory Locations")
    else:
        loc = invelectronics.inventory_locations[int(location_idx)]
        stage = {'loc': loc,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path="/"),
                                 Crumb(name="Status", path="location/"),
                                 Crumb(name=loc.name, path="location/" + location_idx)],  # noqa
                 }
        return render_template('location_detail.html', stage=stage,
                               pagetitle="Inventory Location " + loc.name)
