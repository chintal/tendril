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

import os
from urllib import urlencode
from urllib2 import unquote
from collections import namedtuple

from flask import render_template, abort, request
from flask import redirect, url_for
from flask import jsonify
from flask_user import login_required

from tendril.entityhub.supersets import _group_by_pcbname
from tendril.entityhub.supersets import _status_filter
import tendril.gedaif.gsymlib

from . import gsymlib as blueprint

from tendril.entityhub import supersets
from tendril.utils.fsutils import get_path_breadcrumbs
from tendril.utils.fsutils import Crumb
from tendril.utils.config import GEDA_SYMLIB_ROOT
from tendril.inventory.electronics import get_inventory_stage


def is_geda_folder(path):
    if path is not None:
        path = os.path.join(GEDA_SYMLIB_ROOT, path)
    else:
        path = GEDA_SYMLIB_ROOT
    if os.path.isdir(path):
        return True
    return False

Subfolder = namedtuple('Subfolder', 'name path')


def get_geda_browser_context(path):
    if not is_geda_folder(path):
        abort(404)
    if path is not None:
        path = os.path.join(GEDA_SYMLIB_ROOT, path)
    else:
        path = GEDA_SYMLIB_ROOT

    flatten_folders = False
    flatten_folders_st = 'off'
    if request.args.get('flattenFolders') == u'on':
        flatten_folders = True
        flatten_folders_st = 'on'

    resolve_generators = False
    resolve_generators_st = 'off'
    if request.args.get('resolveGenerators') == u'on':
        resolve_generators = True
        resolve_generators_st = 'on'

    show_generators = True
    hide_generators = False
    hide_generators_st = 'off'
    if request.args.get('hideGenerators') == u'on':
        show_generators = False
        hide_generators = True
        hide_generators_st = 'on'

    show_images = False
    show_images_st = 'off'
    if request.args.get('showImages') == u'on':
        show_images = True
        show_images_st = 'on'

    if not flatten_folders:
        subfolders = [Subfolder(name=x, path=os.path.relpath(os.path.join(path, x), GEDA_SYMLIB_ROOT))  # noqa
                      for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]  # noqa
    else:
        subfolders = []

    symbols = tendril.gedaif.gsymlib.gen_symlib(path,
                                                include_generators=show_generators,  # noqa
                                                resolve_generators=resolve_generators,  # noqa
                                                recursive=flatten_folders)
    if symbols is None:
        symbols = []

    queryst = urlencode({'showImages': show_images_st,
                         'hideGenerators': hide_generators_st,
                         'resolveGenerators': resolve_generators_st,
                         'flattenFolders': flatten_folders_st})

    breadcrumbs = get_path_breadcrumbs(path, GEDA_SYMLIB_ROOT,
                                       rootst="gEDA Symbol Library",
                                       prefix='browse')

    context = {'path': os.path.relpath(path, GEDA_SYMLIB_ROOT),
               'subfolders': sorted(subfolders, key=lambda y: y.name),
               'breadcrumbs': breadcrumbs,
               'symbols': sorted(symbols, key=lambda y: y.ident),
               'show_images': show_images,
               'resolve_generators': resolve_generators,
               'hide_generators': hide_generators,
               'flatten_folders': flatten_folders,
               'query_string': queryst}
    return context


def get_geda_symbol_context(ident):
    symbol = tendril.gedaif.gsymlib.get_symbol(ident, get_all=True)
    symbol = [x for x in symbol if x.status != 'Generator']

    navpath = os.path.relpath(symbol[0].fpath, GEDA_SYMLIB_ROOT)
    navpath = os.path.join('browse', navpath)
    breadcrumbs = get_path_breadcrumbs(navpath, rootst="gEDA Symbol Library")
    if symbol[0].is_virtual:
        breadcrumbs.insert(-1, Crumb(name=os.path.splitext(symbol[0].fname)[0] + '.gen',  # noqa
                                     path='detail/' + os.path.splitext(symbol[0].fname)[0] + '.gen'))  # noqa

    stage = {'ident': ident,
             'symbol': symbol[0],
             'sympaths': [os.path.relpath(sym.fpath, GEDA_SYMLIB_ROOT) for sym in symbol],  # noqa
             'imgpaths': [sym.img_repr_fname for sym in symbol],
             'inclusion': supersets.get_symbol_inclusion(ident),
             'breadcrumbs': breadcrumbs}

    stage.update(get_inventory_stage(ident))
    return stage


def get_geda_generator_context(gen):
    generator = tendril.gedaif.gsymlib.get_generator(gen)
    navpath = os.path.relpath(generator.fpath, GEDA_SYMLIB_ROOT)
    navpath = os.path.splitext(navpath)[0] + '.gen'
    navpath = os.path.join('browse', navpath)
    genobj = tendril.gedaif.gsymlib.GSymGeneratorFile(generator.fpath)

    return {'genname': gen,
            'generator': generator,
            'breadcrumbs': get_path_breadcrumbs(navpath, rootst="gEDA Symbol Library"),  # noqa
            'sympaths': [os.path.relpath(generator.fpath, GEDA_SYMLIB_ROOT)],
            'genpath': os.path.relpath(generator.genpath, GEDA_SYMLIB_ROOT),
            'genobj': genobj}


def get_geda_subcircuit_context(sc):
    subcircuit = tendril.gedaif.gsymlib.get_subcircuit(sc)
    navpath = os.path.relpath(subcircuit.fpath, GEDA_SYMLIB_ROOT)
    navpath = os.path.splitext(navpath)[0] + '.sc'
    navpath = os.path.join('browse', navpath)
    return {'ident': subcircuit.subcircuitident,
            'symbol': subcircuit,
            'breadcrumbs': get_path_breadcrumbs(navpath, rootst="gEDA Symbol Library"),  # noqa
            'imgpath': subcircuit.img_repr_fname,
            'schimgpath': subcircuit.sch_img_repr_fname
           }


@blueprint.route('/detail/<path:sc>.sc')
@login_required
def view_subcircuit(sc=None):
    stage = {'crumbroot': "/gsymlib"}
    if sc is not None:
        sc = unquote(sc)
        if sc in tendril.gedaif.gsymlib.subcircuit_names:
            stage.update(get_geda_subcircuit_context(sc))
            return render_template('gsymlib_subcircuit.html', stage=stage,
                                   pagetitle='gEDA Subcircuit Detail')
    abort(404)


@blueprint.route('/detail/<path:gen>.gen')
@login_required
def view_generator(gen=None):
    stage = {'crumbroot': "/gsymlib"}
    if gen is not None:
        gen += '.gen'
        gen = unquote(gen)
        if gen in tendril.gedaif.gsymlib.generator_names:
            stage.update(get_geda_generator_context(gen))
            return render_template('gsymlib_generator.html', stage=stage,
                                   pagetitle='gEDA Generator Detail')
    abort(404)


@blueprint.route('/detail/<path:ident>')
@login_required
def view_symbol(ident=None):
    stage = {'crumbroot': "/gsymlib"}
    if ident is not None:
        ident = unquote(ident)
        if ident in tendril.gedaif.gsymlib.gsymlib_idents:
            stage.update(get_geda_symbol_context(ident))
            return render_template('gsymlib_symbol.html', stage=stage,
                                   pagetitle='gEDA Symbol Detail ' + ident)
    abort(404)


@blueprint.route('/browse/')
@blueprint.route('/browse/<path:path>')
@login_required
def view_browse(path=None):
    stage = {'crumbroot': "/gsymlib"}

    if path is None:
        stage.update(get_geda_browser_context(None))
        return render_template('gsymlib_browse.html', stage=stage,
                               pagetitle='gEDA Library Browser')

    if path is not None and is_geda_folder(path):
        stage.update(get_geda_browser_context(path))
        return render_template('gsymlib_browse.html', stage=stage,
                               pagetitle='gEDA Library Browser')

    abort(404)


@blueprint.route('/idents.json')
@login_required
def json_idents():
    lidents = list(tendril.gedaif.gsymlib.gsymlib_idents)
    lidents = sorted(lidents)
    return jsonify(idents=lidents)


@blueprint.route('/', methods=['GET', 'POST'])
@login_required
def view_main():
    ferror = False
    if request.method == 'POST':
        ident = request.form['ident']
        if tendril.gedaif.gsymlib.is_recognized(ident):
            return redirect(url_for('.view_symbol', ident=ident))
        ferror = True
    stage = {'ferror': ferror,
             'crumbroot': "/gsymlib",
             'recent_symbols': tendril.gedaif.gsymlib.get_latest_symbols()}
    return render_template('gsymlib_main.html', stage=stage,
                           pagetitle='gEDA Symbol Library')
