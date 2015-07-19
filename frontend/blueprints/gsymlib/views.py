"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
from urllib import urlencode
from urllib2 import unquote
from collections import namedtuple

from flask import render_template, abort, request
from flask_user import login_required

import gedaif.gsymlib

from . import gsymlib as blueprint

from utils.fs import get_path_breadcrumbs
from utils.fs import Crumb
from utils.config import GEDA_SYMLIB_ROOT


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
        subfolders = [Subfolder(name=x, path=os.path.relpath(os.path.join(path, x), GEDA_SYMLIB_ROOT))
                      for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
    else:
        subfolders = []

    symbols = gedaif.gsymlib.gen_symlib(path,
                                        include_generators=show_generators,
                                        resolve_generators=resolve_generators,
                                        recursive=flatten_folders)
    if symbols is None:
        symbols = []

    queryst = urlencode({'showImages': show_images_st,
                         'hideGenerators': hide_generators_st,
                         'resolveGenerators': resolve_generators_st,
                         'flattenFolders': flatten_folders_st})

    context = {'path': os.path.relpath(path, GEDA_SYMLIB_ROOT),
               'subfolders': sorted(subfolders, key=lambda y: y.name),
               'breadcrumbs': get_path_breadcrumbs(path, GEDA_SYMLIB_ROOT, rootst="gEDA Symbol Library"),
               'symbols': sorted(symbols, key=lambda y: y.ident),
               'show_images': show_images,
               'resolve_generators': resolve_generators,
               'hide_generators': hide_generators,
               'flatten_folders': flatten_folders,
               'query_string': queryst}

    return context


def get_geda_symbol_context(ident):
    symbol = gedaif.gsymlib.get_symbol(ident, get_all=True)
    symbol = [x for x in symbol if x.status != 'Generator']

    navpath = os.path.relpath(symbol[0].fpath, GEDA_SYMLIB_ROOT)
    breadcrumbs = get_path_breadcrumbs(navpath, rootst="gEDA Symbol Library")
    if symbol[0].is_virtual:
        breadcrumbs.insert(-1, Crumb(name=os.path.splitext(symbol[0].fname)[0] + '.gen',
                                     path='detail/' + os.path.splitext(symbol[0].fname)[0] + '.gen'))

    return {'ident': ident,
            'symbol': symbol[0],
            'sympaths': [os.path.relpath(sym.fpath, GEDA_SYMLIB_ROOT) for sym in symbol],
            'imgpaths': [sym.img_repr_fname for sym in symbol],
            'breadcrumbs': breadcrumbs}


def get_geda_generator_context(gen):
    generator = gedaif.gsymlib.get_generator(gen)
    navpath = os.path.relpath(generator.fpath, GEDA_SYMLIB_ROOT)
    navpath = os.path.splitext(navpath)[0] + '.gen'
    genobj = gedaif.gsymlib.GSymGeneratorFile(generator.fpath)

    return {'genname': gen,
            'generator': generator,
            'breadcrumbs': get_path_breadcrumbs(navpath, rootst="gEDA Symbol Library"),
            'sympaths': [os.path.relpath(generator.fpath, GEDA_SYMLIB_ROOT)],
            'genpath': os.path.relpath(generator.genpath, GEDA_SYMLIB_ROOT),
            'genobj': genobj}


@blueprint.route('/')
@blueprint.route('/detail/<path:gen>.gen')
@blueprint.route('/detail/<path:ident>')
@blueprint.route('/<path:path>')
@login_required
def main(path=None, ident=None, gen=None):
    stage = {'crumbroot': "/gsymlib"}
    if path is None and ident is None and gen is None:
        stage.update(get_geda_browser_context(None))
        return render_template('gsymlib_browse.html', stage=stage,
                               pagetitle='gEDA Library Browser')
    if path is not None and is_geda_folder(path):
        stage.update(get_geda_browser_context(path))
        return render_template('gsymlib_browse.html', stage=stage,
                                pagetitle='gEDA Library Browser')
    if ident is not None:
        ident = unquote(ident)
        if ident in gedaif.gsymlib.gsymlib_idents:
            stage.update(get_geda_symbol_context(ident))
            return render_template('gsymlib_symbol.html', stage=stage,
                                   pagetitle='gEDA Symbol Detail')
    if gen is not None:
        gen += '.gen'
        gen = unquote(gen)
        if gen in gedaif.gsymlib.generator_names:
            stage.update(get_geda_generator_context(gen))
            return render_template('gsymlib_generator.html', stage=stage,
                                   pagetitle='gEDA Generator Detail')
    abort(404)
