"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os

from flask_assets import Bundle, Environment
from frontend.app import app

from utils.config import INSTANCE_CACHE


bundles = {
    'base_css': Bundle(
        'css/normalize.css',
        'css/foundation.css',
        'css/foundation-icons.css',
        'css/responsive-tables.css',
        'css/colors.css',
        'css/koala.css',
        output='gen/base.css',
        filters='cssmin'),

    'base_js': Bundle(
        'js/vendor/modernizr.js',
        'js/vendor/jquery.js',
        output='gen/base.js',
        filters='jsmin'),

    'foundation_js': Bundle(
        'js/foundation/foundation.js',
        'js/foundation/foundation.topbar.js',
        'js/foundation/foundation.dropdown.js',
        'js/foundation/foundation.magellan.js',
        'js/foundation/foundation.equalizer.js',
        'js/foundation/foundation.alert.js',
        'js/vendor/stickyFooter.js',
        'js/vendor/responsive-tables.js',
        'js/vendor/jquery.textfill.js',
        output='gen/foundation.js',
        filters='jsmin')
}


assets = Environment(app)
assets.cache = os.path.join(INSTANCE_CACHE, 'flaskassetcache')
assets.register(bundles)

