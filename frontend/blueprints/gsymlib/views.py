"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from . import gsymlib
from flask_user import login_required


@gsymlib.route('/')
@login_required
def root():
    return "GSYMLIB"
