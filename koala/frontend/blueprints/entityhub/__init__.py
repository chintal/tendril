"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from flask import Blueprint

entityhub = Blueprint('entityhub', __name__,
                      template_folder='templates')

import views  # noqa
