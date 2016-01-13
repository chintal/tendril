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
from flask import request
from flask import abort
from flask_user import login_required
from flask_user import current_user

from . import indent as blueprint

from tendril.dox import indent as dxindent
from tendril.dox import production as dxproduction
from tendril.utils.fsutils import Crumb


@login_required
@blueprint.route('/create', methods=['POST'])
def create_indent():
    # Validate Indent Metadata
        # Requested by is a valid user
        # Date is valid or None
        # Title is valid
        # Sno is valid or None
        # Parent indent sno is valid or None
        # Prod ord sno is valid or None
        # Root ord sno is valid or None
        # Indent for is valid

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
                 'indent_sno': None}
        return render_template('indent_new.html', stage=stage,
                               pagetitle="New Stock Indent")
    else:
        prod_ord_sno = dxindent.get_indent_production_order(serialno=indent_sno)
        root_ord_sno = dxproduction.get_root_order(serialno=prod_ord_sno)
        order_title = dxproduction.get_order_title(serialno=prod_ord_sno)
        sidx = max([int(x.split('.')[1]) for x in
                    dxindent.get_supplementary_indents(serialno=indent_sno)]) + 1
        stage = {'is_supplementary': True,
                 'parent_indent_sno': indent_sno,
                 'prod_order_sno': prod_ord_sno,
                 'root_order_sno': root_ord_sno,
                 'order_title': order_title,
                 'sidx': sidx,
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
        prod_sno = dxindent.get_indent_production_order(serialno=indent_sno)
        cobom = dxindent.get_indent_cobom(serialno=indent_sno)
        stage = {'docs': docs,
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
