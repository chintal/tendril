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

import os

from flask import render_template
from flask import send_file
from flask import send_from_directory
from flask_user import login_required

from tendril.frontend.app import app
from tendril.utils.config import COMPANY_BLACK_LOGO_PATH

from tendril.utils.fsutils import Crumb


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    return render_template('pages/home_page.html')


@app.route('/sourcing/')
@login_required
def landing_sourcing():
    stage = {'crumbroot': '/sourcing',
             'breadcrumbs': [Crumb(name="Sourcing", path="")],
             }
    return render_template('pages/land_sourcing.html', stage=stage,
                           pagetitle='Sourcing')


@app.route('/inventory/')
@login_required
def landing_inventory():
    stage = {'crumbroot': '/inventory',
             'breadcrumbs': [Crumb(name="Inventory", path="")],
             }
    return render_template('pages/land_inventory.html', stage=stage,
                           pagetitle='Inventory')


@app.route('/instanceassets/logo.png')
def get_instance_logo():
    return send_file(COMPANY_BLACK_LOGO_PATH)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )
