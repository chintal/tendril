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
from flask import redirect
from flask import url_for
from flask_user import login_required

from . import vendors as blueprint
from .forms import SourcingIdentSearch

from tendril.gedaif.gsymlib import get_symbol
from tendril.utils.fsutils import Crumb
from tendril.sourcing.electronics import vendor_list
from tendril.sourcing.electronics import get_vendor_by_name
from tendril.sourcing.electronics import get_sourcing_information
from tendril.sourcing.electronics import SourcingException
from tendril.inventory.guidelines import electronics_qty
from tendril.utils.types.lengths import Length


@blueprint.route('/results', methods=['POST'])
@login_required
def render_search_results():
    form = SourcingIdentSearch()
    if form.validate_on_submit():
        ident = form.ident.data
        qty = form.qty.data

        if not qty:
            qty = electronics_qty.get_compliant_qty(ident, 1)
            form.qty.data = qty
        try:
            qty = int(qty)
        except ValueError:
            qty = Length(qty)

        vl = []
        for vname in form.vendors.data:
            v = get_vendor_by_name(vname)
            if not v:
                raise ValueError
            vl.append(v)

        try:
            vsi = get_sourcing_information(
                ident, qty, avendors=vl, allvendors=True,
                get_all=form.get_all.data
            )
        except SourcingException:
            vsi = []

        symbol = get_symbol(ident)

        stage = {'crumbroot': '/sourcing',
                 'breadcrumbs': [
                     Crumb(name="Sourcing", path=""),
                     Crumb(name="Vendors", path="vendors/"),
                     Crumb(name="Search Results", path="vendors/results")],
                 'isinfos': vsi,
                 'ident': ident,
                 'symbol': symbol,
                 }

        return render_template('vendors_search_results.html', stage=stage,
                               form=form, pagetitle='Sourcing Search Results')
    else:
        return redirect(url_for('.main'))


@blueprint.route('/', methods=['GET'])
@login_required
def main():
    form = SourcingIdentSearch()
    stage = {'vendors': vendor_list,
             'crumbroot': '/sourcing',
             'breadcrumbs': [Crumb(name="Sourcing", path=""),
                             Crumb(name="Vendors", path="vendors/")],
             }
    return render_template('vendors_main.html', stage=stage, form=form,
                           pagetitle='Vendors')
