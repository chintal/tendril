"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


from flask import Blueprint

gsymlib = Blueprint('gsymlib', __name__, template_folder='templates')

import views
