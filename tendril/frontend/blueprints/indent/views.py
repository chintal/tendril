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

import os
import arrow
import shutil

from flask import Response
from flask import render_template
from flask import redirect
from flask import url_for
from flask_user import login_required

from tendril.entityhub.serialnos import get_serialno
from tendril.entityhub.serialnos import register_serialno

from tendril.dox.labelmaker import get_manager
from tendril.boms.outputbase import CompositeOutputBom
from tendril.boms.outputbase import create_obom_from_listing
from tendril.inventory.indent import InventoryIndent
from tendril.inventory.indent import AuthChainNotValidError
from tendril.dox import indent as dxindent

from tendril.utils.fsutils import Crumb
from tendril.utils.fsutils import TEMPDIR
from tendril.utils.fsutils import get_tempname
from tendril.utils.db import get_session
from tendril.auth.db.controller import get_username_from_full_name

from . import indent as blueprint
from .forms import CreateIndentForm


@blueprint.route('/<indent_sno>/getlabels')
@login_required
def get_indent_labels(indent_sno=None):
    rindent = InventoryIndent(sno=indent_sno)
    fe_workspace_path = os.path.join(TEMPDIR, 'frontend')
    if not os.path.exists(fe_workspace_path):
        os.makedirs(fe_workspace_path)
    workspace_path = os.path.join(fe_workspace_path, get_tempname())
    os.makedirs(workspace_path)
    labelmanager = get_manager()
    rindent.make_labels(label_manager=labelmanager)
    rfile = labelmanager.generate_pdf(workspace_path, force=True)

    if not rfile:
        return "Didn't get a manifest set!"
    try:
        content = open(rfile).read()
        return Response(content, mimetype="application/pdf")
    except IOError as exc:
        return str(exc)


@login_required
@blueprint.route('/new/<indent_sno>', methods=['POST', 'GET'])
@blueprint.route('/new', methods=['POST', 'GET'])
def new_indent(indent_sno=None):
    form = CreateIndentForm(parent_indent_sno=indent_sno)
    stage = {'crumbroot': '/inventory'}
    if form.validate_on_submit():
        try:
            with get_session() as session:
                sno = form.indent_sno.sno.data
                if not sno:
                    if indent_sno is not None:
                        sno = form.get_supplementary_sno_default()
                        register_serialno(sno=sno, efield="WEB FRONTEND INDENT",
                                          session=session)
                    else:
                        sno = get_serialno(series='IDT',
                                           efield='WEB FRONTEND INDENT',
                                           register=True, session=session)
                else:
                    # additional sno validation?
                    pass
                nindent = InventoryIndent(sno=sno, session=session)
                # Construct COBOM
                obom = create_obom_from_listing(form.components.data,
                                                'MANUAL (WEB)')
                cobom = CompositeOutputBom([obom],
                                           name='MANUAL (WEB) {0}'.format(sno))

                requested_by = get_username_from_full_name(full_name=form.user.data,
                                                           session=session)

                icparams = {
                    'cobom': cobom,
                    'title': form.indent_title.data,
                    'desc': form.indent_desc.data,
                    'requested_by': requested_by,
                    'rdate': form.rdate.data or arrow.utcnow(),
                    'indent_type': form.indent_type.data,
                }
                nindent.create(**icparams)

                root_order_sno = form.root_order_sno.data
                prod_order_sno = form.prod_order_sno.data
                try:
                    nindent.define_auth_chain(prod_order_sno=prod_order_sno,
                                              root_order_sno=root_order_sno,
                                              session=session)
                except AuthChainNotValidError:
                    raise
                nindent.register_auth_chain(session=session)

                fe_workspace_path = os.path.join(TEMPDIR, 'frontend')
                if not os.path.exists(fe_workspace_path):
                    os.makedirs(fe_workspace_path)
                workspace_path = os.path.join(fe_workspace_path, get_tempname())
                os.makedirs(workspace_path)

                nindent.process(outfolder=workspace_path,
                                register=True, session=session)

                shutil.rmtree(workspace_path)
            return redirect(url_for('.indent', indent_sno=str(sno)))
        except AuthChainNotValidError:
            stage['auth_not_valid'] = True

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
                                              path='/'.join(["indent",
                                                             indent_sno,
                                                             "/new"])),
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
        indent_obj = InventoryIndent(indent_sno)
        stage = {'indent': indent_obj,
                 'crumbroot': '/inventory',
                 'breadcrumbs': [Crumb(name="Inventory", path=""),
                                 Crumb(name="Indent", path="indent/"),
                                 Crumb(name=indent_sno, path="indent/" + indent_sno)],  # noqa
                 }
        return render_template('indent_detail.html', stage=stage,
                               pagetitle="Stock Indent " + indent_sno)
