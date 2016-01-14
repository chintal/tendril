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

from . import indent as blueprint
from .forms import CreateIndentForm

from tendril.dox import indent as dxindent
from tendril.utils.fsutils import Crumb


@login_required
@blueprint.route('/new/<indent_sno>', methods=['POST', 'GET'])
@blueprint.route('/new', methods=['POST', 'GET'])
def new_indent(indent_sno=None):
    form = CreateIndentForm(parent_indent_sno=indent_sno)
    if form.validate_on_submit():
        # Construct COBOM

        # Check for Authorization
        # Nothing right now.

        # Create Indent

        # Redirect to Created Indent
        pass
    stage = {'crumbroot': '/inventory'}
    if indent_sno is None:
        stage_crumbs = {'breadcrumbs': [Crumb(name="Inventory", path=""),
                                        Crumb(name="Indent", path="indent/"),
                                        Crumb(name="New", path="indent/new")],
                        }
        pagetitle = "Create New Indent"
    else:

        stage_crumbs = {'breadcrumbs': [Crumb(name="Inventory", path=""),
                                        Crumb(name="Indent", path="indent/"),
                                        Crumb(name=indent_sno,
                                              path="indent/" + indent_sno),
                                        Crumb(name="New",
                                              path="indent/" + indent_sno + "/new"),
                                        ]
                        }
        pagetitle = "New Supplementary Indent for " + indent_sno
    stage.update(stage_crumbs)
    return render_template('indent_new.html', stage=stage, form=form,
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
