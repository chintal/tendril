# -*- coding: utf-8 -*-
# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import json

from future.utils import viewitems
from flask import render_template
from flask import abort, flash
from flask import jsonify
from flask_user import login_required

from . import entityhub as blueprint
from .forms import CreateSnoSeriesForm

from tendril.conventions import status
from tendril.entityhub.modules import get_prototype_lib
from tendril.entityhub.modules import CardPrototype
from tendril.entityhub.modules import CablePrototype

from tendril.entityhub.modules import get_pcb_lib

# TODO Consider migration of the next section of imports
# to a prototype like structure
from tendril.entityhub import projects as ehprojects
from tendril.entityhub import products as ehproducts
from tendril.entityhub import serialnos as ehserialnos
from tendril.entityhub.db.controller import SeriesNotFound

from tendril.dox.gedaproject import get_docs_list
from tendril.dox.gedaproject import get_img_list
from tendril.dox.gedaproject import get_pcbpricing_data

from tendril.inventory import electronics as invelectronics
from tendril.utils.fsutils import Crumb
from tendril.utils.types.currency import BASE_CURRENCY_SYMBOL


@blueprint.route('/modules.json')
@login_required
def modules_list():
    prototypes = get_prototype_lib()
    moduls = sorted(prototypes.keys())
    return jsonify({'modules': moduls})


@blueprint.route('/modules/<modulename>')
@blueprint.route('/modules/')
@login_required
def modules(modulename=None):
    if modulename is None:
        stage = {}
        return render_template('entityhub_modules.html', stage=stage,
                               pagetitle="Modules")
    else:
        # Find appropriate module and redirect to page
        pass


@blueprint.route('/cables/<cblname>')
@blueprint.route('/cables/')
@login_required
def cables(cblname=None):
    prototypes = get_prototype_lib()
    if cblname is None:
        stage_cables = [v for k, v in viewitems(prototypes)
                        if isinstance(v, CablePrototype)]
        stage_cables.sort(key=lambda x: (x.status, x.ident))

        series = {}

        for cable in stage_cables:
            if cable.configs.snoseries not in series.keys():
                series[cable.configs.snoseries] = 1
            else:
                series[cable.configs.snoseries] += 1

        stage = {'series': series,
                 'cables': stage_cables,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Modules", path="modules/"),
                                 Crumb(name="Cables", path="cables/")]
                 }
        return render_template('entityhub_cables.html', stage=stage,
                               pagetitle="Cables")
    else:
        prototype = prototypes[cblname]
        cablefolder = prototype.projfolder
        gcf = prototype.configs
        stage_cable = gcf.configuration(cblname)
        stage_bom = prototype.bom
        stage_docs = get_docs_list(cablefolder, cblname)
        barepcb = gcf.rawconfig['cblname']
        stage = {'name': cblname,
                 'cable': stage_cable,
                 'bom': stage_bom,
                 'refbom': stage_bom.create_output_bom(cblname),
                 'docs': stage_docs,
                 'barepcb': barepcb,
                 'prototype': prototype,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Modules", path="modules/"),
                                 Crumb(name="Cables", path="cables/"),
                                 Crumb(name=cblname, path="cables/"+cblname)]
                 }
        return render_template('entityhub_cable_detail.html', stage=stage,
                               pagetitle=cblname + " Cable Details")


@blueprint.route('/cards/<cardname>')
@blueprint.route('/cards/')
@login_required
def cards(cardname=None):
    prototypes = get_prototype_lib()
    if cardname is None:
        stage_cards = [v for k, v in viewitems(prototypes)
                       if isinstance(v, CardPrototype)]
        stage_cards.sort(key=lambda x: (x.status, x.ident))

        series = {}
        tstatuses = {str(x): 0 for x in status.get_known_statuses()}
        for card in stage_cards:
            if card.configs.snoseries not in series.keys():
                series[card.configs.snoseries] = 1
            else:
                series[card.configs.snoseries] += 1
            tstatuses[str(card.status)] += 1
        statuses = [(x, tstatuses[str(x)]) for x in status.get_known_statuses()]

        stage = {'statuses': statuses,
                 'series': series,
                 'cards': stage_cards,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Modules", path="modules/"),
                                 Crumb(name="Cards", path="cards/")]
                 }
        return render_template('entityhub_cards.html', stage=stage,
                               pagetitle="Cards")
    else:
        prototype = prototypes[cardname]
        cardfolder = prototype.projfolder
        gcf = prototype.configs
        stage_card = gcf.configuration(cardname)
        stage_bom = prototype.bom
        stage_docs = get_docs_list(cardfolder, cardname)
        barepcb = gcf.pcbname
        stage = {'name': cardname,
                 'card': stage_card,
                 'bom': stage_bom,
                 'refbom': stage_bom.create_output_bom(cardname),
                 'docs': stage_docs,
                 'barepcb': barepcb,
                 'prototype': prototype,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Modules", path="modules/"),
                                 Crumb(name="Cards", path="cards/"),
                                 Crumb(name=cardname, path="cards/"+cardname)]
                 }
        return render_template('entityhub_card_detail.html', stage=stage,
                               pagetitle=cardname + " Card Details")


def get_pcb_costing_chart(projectfolder):
    data = get_pcbpricing_data(projectfolder)
    if not data:
        return None
    # TODO Interactive guideline and legend would be nice to have.
    # Keys : dterm
    datasets = {}

    for qty in sorted(data['pricing'].keys()):
        p = data['pricing'][qty]
        for dterm in p.keys():
            if dterm not in datasets.keys():
                datasets[dterm] = []
            datasets[dterm].append({'x': qty, 'y': p[dterm]})

    data = []
    for k, v in viewitems(datasets):
        data.append({
                    'values': v,
                    'key': "{0} days".format(k),
                    'type': 'line',
                    'yAxis': '1',
                    })

    mdata = datasets[10]
    data.append({
        'values': [{'x': a['x'], 'y': a['x'] * a['y']} for a in mdata],
        'key': 'Total @10',
        'type': 'line',
        'yAxis': '2',
    })

    lstage = {'data': data,
              'csymbol': BASE_CURRENCY_SYMBOL}
    return lstage


@blueprint.route('/pcbs/<pcbname>')
@blueprint.route('/pcbs/')
@login_required
def pcbs(pcbname=None):
    pcblib = get_pcb_lib()
    if pcbname is None:
        stage_pcbs = [v for k, v in viewitems(pcblib)]
        stage = {'pcbs': sorted([x for x in stage_pcbs],
                                key=lambda y: (y.status, y.ident)),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/")]}
        return render_template('entityhub_pcbs.html', stage=stage,
                               pagetitle="Bare PCBs")
    else:
        prototype = pcblib[pcbname]
        prototype_lib = get_prototype_lib()
        cobjs = [prototype_lib[x]
                 for x in prototype.configs.configuration_names]
        cobjs.sort(key=lambda y: y.indicative_cost)
        configurations_costing_data = json.dumps(
            [{
                'key': "-2 ^ Sourcing Errors",
                'values': [
                    {'label': x.ident,
                     'value': (2 ** x.sourcing_errors.terrors) * (-1)}
                    for x in cobjs
                    ],
                'color': '#d67777',
            },
             {
                'key': "Indicative Costing",
                'values': [
                    {'label': x.ident, 'value': x.indicative_cost.native_value}
                    for x in cobjs
                ],
                'color': '#4f99b4',
            }]
        )

        stage = {'prototype': prototype,
                 'name': pcbname,
                 'configdata': prototype.configs,
                 'configurations': cobjs,
                 'configurations_costing': configurations_costing_data,
                 'native_currency_symbol': BASE_CURRENCY_SYMBOL,
                 'docs': get_docs_list(prototype.projfolder),
                 'imgs': get_img_list(prototype.projfolder),
                 'costing': get_pcb_costing_chart(prototype.projfolder),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/"),
                                 Crumb(name=pcbname, path="pcbs/" + pcbname)]}

        ident = 'PCB ' + pcbname
        inv_loc_status = {}
        inv_loc_transform = {}
        for loc in invelectronics.inventory_locations:
            qty = loc.get_ident_qty(ident) or 0
            reserve = loc.get_reserve_qty(ident) or 0
            inv_loc_status[loc._code] = (loc._name, qty, reserve, qty-reserve)

            inv_loc_transform[loc._code] = (loc._name,
                                            loc.tf.get_contextual_repr(ident))
        inv_total_reservations = invelectronics.get_total_reservations(ident)
        inv_total_quantity = invelectronics.get_total_availability(ident)
        inv_total_availability = inv_total_quantity - inv_total_reservations

        inv_stage = {
            'inv_loc_status': inv_loc_status,
            'inv_total_reservations': inv_total_reservations,
            'inv_total_quantity': inv_total_quantity,
            'inv_total_availability': inv_total_availability,
            'inv_loc_transform': inv_loc_transform,
            'inv': invelectronics,
        }

        stage.update(inv_stage)

        return render_template('entityhub_pcb_detail.html', stage=stage,
                               pagetitle="PCB Details")


@blueprint.route('/projects/')
@login_required
def projects():
    stage_projects = ehprojects.projects
    stage = {'projects': stage_projects,
             'crumbroot': '/entityhub',
             'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                             Crumb(name="gEDA Projects", path="projects/")]
             }
    return render_template('entityhub_projects.html', stage=stage,
                           pagetitle="gEDA Projects")


@blueprint.route('/products/<productname>')
@blueprint.route('/products/')
@login_required
def products(productname=None):
    if productname is None:
        stage_products = sorted(ehproducts.productlib,
                                key=lambda x: x.name)
        stage = {'products': stage_products,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Products", path="products/")]
                 }
        return render_template('entityhub_products.html', stage=stage,
                               pagetitle="Products")
    else:
        stage = {'product': ehproducts.get_product_by_ident(productname),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Products", path="products/"),
                                 Crumb(name=productname, path="pcbs/" + productname)],  # noqa
                 }
        return render_template('entityhub_product_detail.html', stage=stage,
                               pagetitle="Products")


@blueprint.route('/snoseries/<series>')
@blueprint.route('/snoseries/', methods=('GET', 'POST'))
@login_required
def snoseries(series=None):
    if series is None:
        form = CreateSnoSeriesForm()
        if form.validate_on_submit():
            try:
                ehserialnos.controller.get_series_obj(series=form.series.data)
                alert = 'Did not create series {0}. ' \
                        'Already exists.'.format(form.series.data)
                flash(alert, 'alert')
            except SeriesNotFound:
                ehserialnos.create_serial_series(
                        form.series.data, form.start_seed.data, form.description.data
                )
                alert = 'Created serial series {0}.'.format(form.series.data)
                flash(alert, 'success')

        stage_snoseries = sorted(ehserialnos.get_all_series(), key=lambda x: x.series)
        stage = {'series': stage_snoseries,
                 'crumbroot': '/entityhub',
                 'form': form,
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Serial Series", path="snoseries/")]
                 }
        return render_template('entityhub_snoseries.html', stage=stage,
                               pagetitle="Serial Series")
    else:
        abort(404)
    # else:
    #     stage = {'series': ehproducts.get_product_by_ident(productname),
    #              'crumbroot': '/entityhub',
    #              'breadcrumbs': [Crumb(name="Entity Hub", path=""),
    #                              Crumb(name="Products", path="products/"),
    #                              Crumb(name=productname, path="pcbs/" + productname)],  # noqa
    #              }
    #     return render_template('entityhub_product_detail.html', stage=stage,
    #                            pagetitle="Products")


@blueprint.route('/')
@login_required
def main():
    stage = {}
    return render_template('entityhub_main.html', stage=stage,
                           pagetitle='Entity Hub')
