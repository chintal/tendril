"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import svn.local
import logging
logging.getLogger('svn').setLevel(logging.INFO)


def get_path_revision(p):
    c = svn.local.LocalClient(p)
    return c.info()['commit_revision']


def get_path_repository(p):
    c = svn.local.LocalClient(p)
    return c.info()['repository/root']

