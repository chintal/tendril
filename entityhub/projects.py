"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
import os

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
                lpcbs[cf.configdata['pcbname']] = os.path.join(root, d)
                for config in cf.configdata['configurations']:
                    lcards[config['configname']] = os.path.join(root, d)

    return lprojects, lpcbs, lcards


projects, pcbs, cards = get_projects()
