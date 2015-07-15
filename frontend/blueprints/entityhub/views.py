"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


from flask import render_template, abort, request
from flask_user import login_required

from . import entityhub as blueprint

from utils.fs import get_path_breadcrumbs
from utils.fs import Crumb


@blueprint.route('/')
@login_required
def main():
    stage = {}
    return render_template('entityhub_main.html', stage=stage,
                           pagetitle='Entity Hub')

