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

from . import production as blueprint

from tendril.dox import production as dxproduction
from tendril.utils.fsutils import Crumb


@blueprint.route('/order/<order_sno>')
@blueprint.route('/order/')
@login_required
def results(order_sno=None):
    # Presently only supports getting the latest result. A way to allow
    # any result to be retrieved would be nice.
    if order_sno is None:
        docs = dxproduction.get_all_production_orders()
        stage = {'docs': docs,
                 'crumbroot': '/production',
                 'breadcrumbs': [Crumb(name="Production", path="/"),
                                 Crumb(name="Orders", path="order/")],
                 }
        return render_template('production_orders.html', stage=stage,
                               pagetitle="All Production Orders")
    else:
        docs = dxproduction.get_production_order_docs(order_sno)
        order_yaml, order_snomap = \
            dxproduction.get_production_order_data(order_sno)

        order_indentsno = order_snomap.pop('indentsno')

        stage = {'docs': docs,
                 'order_sno': order_sno,
                 'order_snomap': order_snomap,
                 'order_indentsno': order_indentsno,
                 'order_yaml': order_yaml,
                 'crumbroot': '/production',
                 'breadcrumbs': [Crumb(name="Production", path="/"),
                                 Crumb(name="Orders", path="order/"),
                                 Crumb(name=order_sno, path="order/" + order_sno)],  # noqa
                 }
        return render_template('production_order_detail.html', stage=stage,
                               pagetitle="Production Order " + order_sno)


@blueprint.route('/')
@login_required
def main():
    latest_prod = dxproduction.get_all_production_orders(limit=5)
    stage = {'latest_prod': latest_prod,
             'crumbroot': '/production',
             'breadcrumbs': [Crumb(name="Production", path="/")],
             }
    return render_template('production_main.html', stage=stage,
                           pagetitle='Production')
