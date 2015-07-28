"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os

from flask import Blueprint
from flask_user import login_required

from koala.utils.config import KOALA_ROOT


doc = Blueprint('doc', __name__,
                static_folder=os.path.join(KOALA_ROOT, os.pardir, 'doc', 'build', 'html'))


@doc.route('/')
@login_required
def root():
    return doc.send_static_file('index.html')


@doc.route('/<path:path>')
@login_required
def static_proxy(path):
    # send_static_file will guess the correct MIME type
    return doc.send_static_file(path)
