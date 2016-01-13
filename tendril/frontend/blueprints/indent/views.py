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

import arrow
from arrow.parser import ParserError

from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import abort

from flask_user import login_required
from flask_user import current_user

from . import indent as blueprint
from tendril.frontend.users.controller import get_users_list

from tendril.dox import indent as dxindent
from tendril.dox import production as dxproduction
from tendril.utils.fsutils import Crumb


@login_required
@blueprint.route('/create', methods=['POST'])
def create_indent():
    parent_indent_sno = request.form.get('parent_indent_sno')
    allowed = True
    # Validate Indent Metadata
    # Requested by is a valid user
    if not request.form.get('user') == current_user.full_name:
        if current_user.has_roles('inventory_admin'):
            full_names = [x.full_name for x in get_users_list()]
            if request.form.get('user') in full_names:
                pass
        allowed = False
        flash('Could not authenticate the requesting user. '
              'Please retry.', 'alert')

    # Date is valid or None
    rdate = request.form.get('rdate')
    if rdate:
        try:
            rdate = arrow.get(rdate, 'DD/MM/YYYY')
        except ParserError:
            flash('Could not parse the provided date. '
                  'Please retry.', 'alert')
            allowed = False
    else:
        rdate = arrow.utcnow()

    # Title is valid
    # Sno is valid or None
    # Parent indent sno is valid or None
    # Prod ord sno is valid or None
    # Root ord sno is valid or None
    # Indent for is valid

    if not allowed:
        if parent_indent_sno:
            return redirect(
                    url_for('.new_indent', indent_sno=parent_indent_sno))
        else:
            return redirect(url_for('.new_indent'))

    # Construct COBOM

    # Check for Authorization
    # Nothing right now.

    # Create Indent

    # Redirect to Created Indent
    raise NotImplementedError


@login_required
@blueprint.route('/new/<indent_sno>')
@blueprint.route('/new')
def new_indent(indent_sno=None):
    if indent_sno is None:
        stage = {'is_suplementary': False,
                 'indent_sno': None,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Indent", path="indent/"),
                                 Crumb(name="New", path="indent/new"),
                                 ]}
        return render_template('indent_new.html', stage=stage,
                               pagetitle="New Stock Indent")
    else:
        prod_ord_sno = dxindent.get_indent_production_order(serialno=indent_sno)
        root_ord_sno = dxproduction.get_root_order(serialno=prod_ord_sno)
        parent_indent_sno = dxindent.get_root_indent_sno(serialno=indent_sno)
        order_title = dxproduction.get_order_title(serialno=prod_ord_sno)
        sidx = dxindent.get_new_supplementary_indent_sno(serialno=indent_sno)
        stage = {'is_supplementary': True,
                 'parent_indent_sno': parent_indent_sno,
                 'prod_order_sno': prod_ord_sno,
                 'root_order_sno': root_ord_sno,
                 'order_title': order_title,
                 'sidx': sidx,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Indent", path="indent/"),
                                 Crumb(name=indent_sno,
                                       path="indent/" + indent_sno),
                                 Crumb(name="New",
                                       path="indent/" + indent_sno + "/new"),
                                 ]
                 }
        pagetitle = "New Supplementary Indent for " + indent_sno
        return render_template('indent_new.html', stage=stage,
                               pagetitle=pagetitle)


@blueprint.route('/<indent_sno>')
@blueprint.route('/')
@login_required
def indent(indent_sno=None):
    if indent_sno is None:
        docs = dxindent.get_all_indents_docs()
        stage = {'docs': docs,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Indent", path="indent/")],
                 }
        return render_template('indent.html', stage=stage,
                               pagetitle="All Indents")
    else:
        docs = dxindent.get_indent_docs(indent_sno)
        sindents = dxindent.get_supplementary_indents(indent_sno)
        sindent_docs = dxindent.get_all_indents_docs(snos=sindents)
        prod_sno = dxindent.get_indent_production_order(serialno=indent_sno)
        cobom = dxindent.get_indent_cobom(serialno=indent_sno)
        stage = {'docs': docs,
                 'sindent_docs': sindent_docs,
                 'indent_sno': indent_sno,
                 'prod_sno': prod_sno,
                 'cobom': cobom,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Indent", path="indent/"),
                                 Crumb(name=indent_sno, path="indent/" + indent_sno)],  # noqa
                 }
        return render_template('indent_detail.html', stage=stage,
                               pagetitle="Stock Indent " + indent_sno)
