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

from flask import render_template
from flask_user import login_required
from nvd3 import lineChart

from . import entityhub as blueprint

from tendril.entityhub import projects as ehprojects
from tendril.entityhub import products as ehproducts

from tendril.boms.electronics import import_pcb
from tendril.dox.gedaproject import get_docs_list
from tendril.dox.gedaproject import get_img_list
from tendril.dox.gedaproject import get_pcbpricing_data
from tendril.gedaif.conffile import ConfigsFile

from tendril.utils.fsutils import Crumb
from tendril.utils.types.currency import BASE_CURRENCY_SYMBOL


@blueprint.route('/cards/<cardname>')
@blueprint.route('/cards/')
@login_required
def cards(cardname=None):
    if cardname is None:
        stage_cards = [{'name': k,
                        'detail': ConfigsFile(v).configuration(k)}
                       for k, v in ehprojects.cards.iteritems()
                       if ConfigsFile(v).is_pcb]

        stage_cables = [{'name': k,
                         'detail': ConfigsFile(v).configuration(k)}
                        for k, v in ehprojects.cards.iteritems()
                        if ConfigsFile(v).is_cable]

        stage = {'cards': sorted(stage_cards, key=lambda x: x['name']),
                 'cables': sorted(stage_cables, key=lambda x: x['name']),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Cards", path="cards/")]
                 }
        return render_template('entityhub_cards.html', stage=stage,
                               pagetitle="Cards")
    else:
        cardfolder = ehprojects.cards[cardname]
        gcf = ConfigsFile(cardfolder)
        stage_card = gcf.configuration(cardname)
        stage_bom = import_pcb(cardfolder)
        stage_bom.configure_motifs(cardname)
        stage_docs = get_docs_list(cardfolder, cardname)

        if gcf.is_pcb:
            barepcb = gcf.configdata['pcbname']
        elif gcf.is_cable:
            barepcb = gcf.configdata['cblname']
        else:
            raise ValueError("Doesn't seem to be a card or a cable : " +
                             cardname)
        stage = {'name': cardname,
                 'card': stage_card,
                 'bom': stage_bom,
                 'refbom': stage_bom.create_output_bom(cardname),
                 'docs': stage_docs,
                 'barepcb': barepcb,
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Cards", path="cards/"),
                                 Crumb(name=cardname, path="cards/"+cardname)]
                 }
        return render_template('entityhub_card_detail.html', stage=stage,
                               pagetitle=cardname + " Card Details")


def get_pcb_costing_chart(projectfolder):
    data = get_pcbpricing_data(projectfolder)
    if not data:
        return None
    # TODO Figure out how to have a second y-axis for the total.
    # Keys : dterm
    datasets = {}

    for qty in sorted(data['pricing'].keys()):
        p = data['pricing'][qty]
        for dterm in p.keys():
            if dterm not in datasets.keys():
                datasets[dterm] = {}
            datasets[dterm][qty] = p[dterm]

    chart = lineChart(name="costingChart", x_is_date=False,
                      jquery_on_ready=True,
                      use_interactive_guideline=True,
                      y_axis_format="function(d) { return '" +
                                    BASE_CURRENCY_SYMBOL +
                                    "' + d3.format(',f')(d)}",
                      y_custom_format=True,
                      height=300,
                      )

    for dterm in datasets.keys():
        x_data = sorted(datasets[dterm].keys())
        y_data = [datasets[dterm][x] for x in x_data]
        chart.add_serie(y=y_data, x=x_data, name=str(dterm) + ' days')

    x_data = sorted(datasets[10].keys())
    totals = [(y * x_data[i]) for i, y in
              enumerate([datasets[10][x] for x in x_data])]
    chart.add_serie(y=totals, x=x_data, name='Total@10')

    chart.buildcontent()
    return chart.htmlcontent


@blueprint.route('/pcbs/<pcbname>')
@blueprint.route('/pcbs/')
@login_required
def pcbs(pcbname=None):
    if pcbname is None:
        stage_pcbs = [{'name': k,
                       'configdata': ConfigsFile(v)}
                      for k, v in ehprojects.pcbs.iteritems()]
        stage = {'pcbs': sorted([x for x in stage_pcbs if x['configdata'].status == 'Experimental'],  # noqa
                                key=lambda y: y['name']) +
                         sorted([x for x in stage_pcbs if x['configdata'].status == 'Active'],  # noqa
                                key=lambda y: y['name']) +
                         sorted([x for x in stage_pcbs if x['configdata'].status == 'WIP'],  # noqa
                                key=lambda y: y['name']) +
                         sorted([x for x in stage_pcbs if x['configdata'].status == 'Deprecated'],  # noqa
                                key=lambda y: y['name']),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/")]}
        return render_template('entityhub_pcbs.html', stage=stage,
                               pagetitle="Bare PCBs")
    else:
        stage = {'name': pcbname,
                 'configdata': ConfigsFile(ehprojects.pcbs[pcbname]),
                 'docs': get_docs_list(ehprojects.pcbs[pcbname]),
                 'imgs': get_img_list(ehprojects.pcbs[pcbname]),
                 'costing': get_pcb_costing_chart(ehprojects.pcbs[pcbname]),
                 'crumbroot': '/entityhub',
                 'breadcrumbs': [Crumb(name="Entity Hub", path=""),
                                 Crumb(name="Bare PCBs", path="pcbs/"),
                                 Crumb(name=pcbname, path="pcbs/" + pcbname)]}
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


@blueprint.route('/')
@login_required
def main():
    stage = {}
    return render_template('entityhub_main.html', stage=stage,
                           pagetitle='Entity Hub')
