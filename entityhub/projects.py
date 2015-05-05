"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
import os
import re
import csv

from utils.config import PROJECTS_ROOT
from utils.config import KOALA_ROOT
from gedaif import conffile


def is_project_folder(folder):
    try:
        conffile.ConfigsFile(folder)
    except conffile.NoGedaProjectException:
        return False
    return True


def get_project_doc_folder(projectfolder):
    try:
        conffile.ConfigsFile(projectfolder)
    except conffile.NoGedaProjectException:
        return os.path.join(KOALA_ROOT, 'scratch', 'lostandfound')
    pth = os.path.join(projectfolder, 'doc')
    if not os.path.exists(pth):
        os.makedirs(pth)
    if not os.path.exists(os.path.join(pth, 'confdocs')):
        os.makedirs(os.path.join(pth, 'confdocs'))
    return pth


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
    allfiles = os.listdir(pricingfolder)
    pfrex = re.compile(cardname + "~(.*).csv")
    pfiles = [os.path.join(pricingfolder, x) for x in allfiles if pfrex.match(x)]
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

    if basefolder is None:
        basefolder = PROJECTS_ROOT

    for root, dirs, files in os.walk(basefolder):
        dirs[:] = [d for d in dirs if not d.endswith('.git')]
        for d in dirs:
            if is_project_folder(os.path.join(root, d)):
                lprojects[os.path.relpath(os.path.join(root, d), basefolder)] = os.path.join(root, d)
                cf = conffile.ConfigsFile(os.path.join(root, d))
                if cf.configdata['pcbname'] is not None:
                    lpcbs[cf.configdata['pcbname']] = os.path.join(root, d)
                for config in cf.configdata['configurations']:
                    lcards[config['configname']] = os.path.join(root, d)

    return lprojects, lpcbs, lcards


projects, pcbs, cards = get_projects()
