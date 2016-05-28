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

from flask import Flask

from tendril.frontend.startup.warmup import warm_up_caches


# Warm up caches
warm_up_caches()


# This is the WSGI compliant web application object
app = Flask(__name__)

try:
    from tendril.utils.config import ENABLE_APPENLIGHT
    if ENABLE_APPENLIGHT is True:
        from tendril.utils.config import APPENLIGHT_PRIVATE_API_KEY
        import appenlight_client.ext.flask as appenlight
        app = appenlight.add_appenlight(
            app, {'appenlight.api_key': APPENLIGHT_PRIVATE_API_KEY}
        )
except ImportError:
    APPENLIGHT_API_KEY = None
    appenlight = None
