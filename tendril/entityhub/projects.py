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
import re
import csv

from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.vcs import get_path_revision
from tendril.gedaif import conffile
from tendril.boms.electronics import import_pcb
from tendril.boms.outputbase import CompositeOutputBom

from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)


def is_project_folder(folder):
    try:
        conffile.ConfigsFile(folder)
    except conffile.NoGedaProjectError:
        return False
    return True


def parse_total_costing(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        header = None
        for line in reader:
            if line[0] == 'Ident':
                header = line
                break
        if header is None:
            raise ValueError
        costt = 0
        identc = 0
        uncostedc = 0
        for line in reader:
            if line[0] is not None:
                if line[header.index('Line Price')].strip() == '':
                    uncostedc += 1
                else:
                    costt += float(line[header.index('Line Price')])
                identc += 1
        return costt, identc, uncostedc


def get_card_indicative_cost(cardname):
    projectfolder = cards[cardname]
    pricingfolder = os.path.join(projectfolder, 'doc', 'pricing')
    if not os.path.exists(pricingfolder):
        return None
    allfiles = os.listdir(pricingfolder)
    pfrex = re.compile(cardname + "~(.*).csv")
    pfiles = [os.path.join(pricingfolder, x)
              for x in allfiles if pfrex.match(x)]
    contextc = len(pfiles)
    if contextc == 0:
        return None
    costt = 0
    for fpath in pfiles:
        rval = parse_total_costing(fpath)
        costt += rval[0]
    costt /= contextc
    return costt


def get_projects(basefolder=None):
    lcards = {}
    lpcbs = {}
    lprojects = {}
    lcard_reporoot = {}

    if basefolder is None:
        basefolder = PROJECTS_ROOT

    for root, dirs, files in os.walk(basefolder):
        dirs[:] = [d for d in dirs
                   if not d.endswith('.git') and not d.endswith('.svn')]
        for d in dirs:
            if is_project_folder(os.path.join(root, d)):
                lprojects[
                    os.path.relpath(os.path.join(root, d), basefolder)
                ] = os.path.join(root, d)
                cf = conffile.ConfigsFile(os.path.join(root, d))
                if cf.is_pcb:
                    lpcbs[cf.pcbname] = os.path.join(root, d)
                for config in cf.configuration_names:
                    lcards[config] = os.path.join(root, d)
                    lcard_reporoot[config] = \
                        os.path.relpath(os.path.join(root, d), basefolder)

    return lprojects, lpcbs, lcards, lcard_reporoot


projects, pcbs, cards, card_reporoot = get_projects()

superset_cobom = None


def get_bom_superset(regen=False):
    global superset_cobom
    if not regen and superset_cobom is not None:
        return superset_cobom
    boms = []
    logger.info("Building superset composite BOM")
    for card, path in cards.iteritems():
        logger.debug("Getting BOM for {0}".format(card))
        bom = import_pcb(path)
        obom = bom.create_output_bom(card)
        boms.append(obom)
    logger.info("Collating into superset composite BOM")
    superset_cobom = CompositeOutputBom(boms, name='ALL')
    superset_cobom.collapse_wires()
    return superset_cobom


def get_module_config(modulename):
    if modulename not in cards.keys():
        raise KeyError("Couldn't find {0} in the library!".format(modulename))
    gcf = conffile.ConfigsFile(cards[modulename])
    return gcf


def get_module_snoseries(modulename):
    cf = get_module_config(modulename)
    return cf.snoseries


def check_module_is_card(modulename):
    cf = get_module_config(modulename)
    return cf.is_pcb


def check_module_is_cable(modulename):
    cf = get_module_config(modulename)
    return cf.is_cable


def get_project_repo_repr(modulename):
    repo = card_reporoot[modulename]
    rev = get_path_revision(os.path.join(PROJECTS_ROOT, repo))
    return "{0}::r{1}".format(repo, rev)
