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

from tendril.utils.config import WARM_UP_CACHES
from tendril.frontend.startup.warmup import warm_up_caches

# Warm up caches
if WARM_UP_CACHES is True:
    warm_up_caches()

# This is the WSGI compliant web application object
app = Flask(__name__)
