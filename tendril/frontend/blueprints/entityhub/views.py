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
from tendril.entityhub.modules import get_project_lib

# TODO Consider migration of the next section of imports
# to a prototype like structure
from tendril.entityhub import products as ehproducts
from tendril.entityhub import serialnos as ehserialnos
from tendril.entityhub.db.controller import SeriesNotFound

from tendril.dox.gedaproject import get_img_list
from tendril.dox.gedaproject import get_pcbpricing_data

from tendril.inventory.electronics import get_inventory_stage
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
        stage = {'prototype': prototype,
                 'inclusion': ehproducts.get_module_inclusion(cblname),
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
        stage = {'prototype': prototype,
                 'inclusion': ehproducts.get_module_inclusion(cardname),
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


def _get_configurations_stage(prototype):
    prototype_lib = get_prototype_lib()
    cobjs = [prototype_lib[x]
             for x in prototype.configs.configuration_names]
    cobjs.sort(key=lambda y: y.indicative_cost)
    configurations_costing_data = json.dumps(
        [{
            'key': "Sourcing Errors",
            'values': [
                {'label': x.ident,
                 'value': (2 ** x.sourcing_errors.terrors) * (-1)}
                for x in cobjs
                ],
            'color': '#d67777',
        }, {
            'key': "Indicative Costing",
            'values': [
                {'label': x.ident,
                 'value': x.indicative_cost.native_value}
                for x in cobjs
                ],
            'color': '#4f99b4',
        }]
    )
    return {'configurations': cobjs,
            'configurations_costing': configurations_costing_data,
            'native_currency_symbol': BASE_CURRENCY_SYMBOL,
            }


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
        stage = {'prototype': prototype,
                 'imgs': get_img_list(prototype.projfolder),
                 'costing': get_pcb_costing_chart(prototype.projfolder),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/"),
                                 Crumb(name=pcbname, path="pcbs/" + pcbname)]}
        ident = 'PCB ' + pcbname
        stage.update(get_inventory_stage(ident))
        return render_template('entityhub_pcb_detail.html', stage=stage,
                               pagetitle="PCB Detail {0}".format(pcbname))


@blueprint.route('/projects/<projectname>')
@blueprint.route('/projects/')
@login_required
def projects(projectname=None):
    projectlib = get_project_lib()
    if projectname is None:
        stage_projects = projectlib
        stage = {'projects': stage_projects,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="EDA Projects", path="projects/")]
                 }
        return render_template('entityhub_projects.html', stage=stage,
                               pagetitle="EDA Projects")
    else:
        prototype = projectlib[projectname]
        stage = {'prototype': prototype,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="EDA Projects", path="projects/"),
                                 Crumb(name=projectname, path="projects/" + projectname)]}
        stage.update(_get_configurations_stage(prototype))
        return render_template('entityhub_project_detail.html', stage=stage,
                               pagetitle="Project Details {0}".format(projectname))


@blueprint.route('/products/<productname>')
@blueprint.route('/products/')
@login_required
def products(productname=None):
    if productname is None:
        stage_products = sorted(ehproducts.productlib,
                                key=lambda x: (x.info.status, x.name))
        lines = {}
        ptypes = {}
        tstatuses = {str(x): 0 for x in status.get_known_statuses()}
        for product in stage_products:
            if product.info.ptype not in ptypes.keys():
                ptypes[product.info.ptype] = 1
            else:
                ptypes[product.info.ptype] += 1
            if product.info.line not in lines.keys():
                lines[product.info.line] = 1
            else:
                lines[product.info.line] += 1
            tstatuses[str(product.status)] += 1
        statuses = [(x, tstatuses[str(x)]) for x in status.get_known_statuses()]
        stage = {'statuses': statuses,
                 'lines': lines,
                 'ptypes': ptypes,
                 'products': stage_products,
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
                               pagetitle="Product Detail {0}".format(productname))


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
