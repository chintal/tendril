"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from flask_assets import Bundle, Environment
from frontend.app import app


bundles = {
    'base_css': Bundle(
        'css/normalize.css',
        'css/foundation.css',
        'css/foundation-icons.css',
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
        output='gen/foundation.js',
        filters='jsmin')
}


assets = Environment(app)
assets.register(bundles)
