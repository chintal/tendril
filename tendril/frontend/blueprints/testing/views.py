#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for views
"""

from flask import render_template
from flask_user import login_required

from . import testing as blueprint

from tendril.dox import testing as dxtesting
from tendril.utils.fsutils import Crumb


@blueprint.route('/result/<device_sno>')
@blueprint.route('/result/')
@login_required
def results(device_sno=None):
    # Presently only supports getting the latest result. A way to allow
    # any result to be retrieved would be nice.
    if device_sno is None:
        docs = dxtesting.get_all_test_reports()
        stage = {'docs': docs,
                 'crumbroot': '/testing',
                 'breadcrumbs': [Crumb(name="Testing", path="/"),
                                 Crumb(name="Results", path="result/")],
                 }
        return render_template('test_results.html', stage=stage,
                               pagetitle="All Test Results")
    else:
        docs = dxtesting.get_latest_test_report(device_sno)
        stage = {'docs': docs,
                 'crumbroot': '/testing',
                 'breadcrumbs': [Crumb(name="Testing", path="/"),
                                 Crumb(name="Reports", path="result/"),
                                 Crumb(name=device_sno, path="result/" + device_sno)],  # noqa
                 }
        return render_template('test_result_detail.html', stage=stage,
                               pagetitle=device_sno + " Test Result")


@blueprint.route('/')
@login_required
def main():
    latest = dxtesting.get_all_test_reports(limit=5)
    stage = {'latest': latest,
             'crumbroot': '/testing',
             'breadcrumbs': [Crumb(name="Testing", path="/")],
             }
    return render_template('testing_main.html', stage=stage,
                           pagetitle='Testing')
