"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
from flask import Blueprint
from utils.config import INSTANCE_CACHE


gsymlib = Blueprint('gsymlib', __name__,
                    template_folder='templates',
                    static_folder=os.path.join(INSTANCE_CACHE, 'gsymlib'))

import views
