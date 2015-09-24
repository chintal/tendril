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
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import os

from flask_assets import Bundle, Environment
from tendril.frontend.app import app

from tendril.utils.config import INSTANCE_CACHE


bundles = {
    'base_css': Bundle(
        'css/normalize.css',
        'css/foundation.css',
        'css/colors.css',
        output='gen/base.css',
        filters='cssmin'),

    'base_js': Bundle(
        'js/vendor/modernizr.js',
        'js/vendor/jquery.js',
        'js/vendor/jquery.textfill.js',
        output='gen/base.js',
        filters='jsmin'),

    'foundation_js': Bundle(
        'js/foundation/foundation.js',
        'js/foundation/foundation.topbar.js',
        'js/foundation/foundation.dropdown.js',
        'js/foundation/foundation.magellan.js',
        'js/foundation/foundation.equalizer.js',
        'js/foundation/foundation.alert.js',
        'js/foundation/foundation.tooltip.js',
        'js/vendor/stickyFooter.js',
        output='gen/foundation.js',
        filters='jsmin'),

    'datatables_css': Bundle(
        'css/datatables/dataTables.foundation.css',
        'css/datatables/responsive.foundation.css',
        'css/datatables/buttons.foundation.css',
        'css/datatables/select.foundation.css',
        'css/datatables/keyTable.foundation.css',
        output='gen/datatables.css',
        filters='cssmin'),

    'datatables_js': Bundle(
        'js/datatables/jquery.dataTables.js',
        'js/datatables/dataTables.foundation.js',
        'js/datatables/dataTables.responsive.js',
        'js/datatables/jszip.js',
        'js/datatables/pdfmake.js',
        'js/datatables/vfs_fonts.js',
        'js/datatables/dataTables.buttons.js',
        'js/datatables/buttons.print.js',
        'js/datatables/buttons.html5.js',
        'js/datatables/buttons.colVis.js',
        'js/datatables/buttons.foundation.js',
        'js/datatables/dataTables.select.js',
        'js/datatables/dataTables.keyTable.js',
        output='gen/datatables.js',
        filters='jsmin'),

    'tendril_css': Bundle(
        'css/tendril.css',
        output='gen/tendril.css',
        filters='cssmin'),
}


assets = Environment(app)
assets.cache = os.path.join(INSTANCE_CACHE, 'flaskassetcache')
assets.register(bundles)
