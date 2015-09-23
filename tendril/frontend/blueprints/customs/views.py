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

from . import customs as blueprint

from tendril.dox import customs as dxcustoms
from tendril.dox import docstore
from tendril.entityhub import serialnos
from tendril.utils.fsutils import Crumb


@blueprint.route('/invoice/<invoice_sno>')
@blueprint.route('/invoice/')
@login_required
def invoices(invoice_sno=None):
    if invoice_sno is None:
        snos = dxcustoms.get_all_customs_invoice_serialnos()
        stage = {'snos': snos,
                 'crumbroot': '/sourcing',
                 'breadcrumbs': [Crumb(name="Sourcing", path="main.html"),
                                 Crumb(name="Customs", path="customs/"),
                                 Crumb(name="Invoices", path="customs/inv/")],
                 }
        return render_template('customs_invoices.html', stage=stage,
                               pagetitle="Customs Document Sets")
    else:
        sno = serialnos.get_serialno_object(sno=invoice_sno)
        docs = docstore.get_docs_list_for_serialno(invoice_sno)
        invoice = dxcustoms.get_customs_invoice(invoice_sno)
        stage = {'sno': sno,
                 'docs': docs,
                 'invoice': invoice,
                 'crumbroot': '/sourcing',
                 'breadcrumbs': [Crumb(name="Sourcing", path="main.html"),
                                 Crumb(name="Customs", path="customs/"),
                                 Crumb(name="Invoices", path="customs/invoice/"),  # noqa
                                 Crumb(name=invoice_sno, path="customs/invoice/" + invoice_sno)],  # noqa
                 }
        return render_template(
            'customs_invoice_detail.html', stage=stage,
            pagetitle=invoice_sno + " Customs Document Set"
        )


@blueprint.route('/')
@login_required
def main():
    latest = dxcustoms.get_all_customs_invoice_serialnos(limit=5)
    stage = {'latest': latest,
             'crumbroot': '/sourcing',
             'breadcrumbs': [Crumb(name="Sourcing", path="main.html"),
                             Crumb(name="Customs", path="customs/")],
             }
    return render_template('customs_main.html', stage=stage,
                           pagetitle='Customs')
