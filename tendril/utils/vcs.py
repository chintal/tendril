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
The VCS Utils Module (:mod:`tendril.utils.vcs`)
===============================================

This module provides utilities to deal with version control systems. For the
most part, this module basically proxies specific requests to various other
third-party or python libraries.

Presently, only SVN is supported. Support for git may be added in the future.

"""

import svn.local
import logging
logging.getLogger('svn').setLevel(logging.INFO)


def get_path_revision(p):
    """
    Get the VCS revision for the file at path ``p``.

    :param p: path
    :return: The revision for the repository the file is part of.

    """
    c = svn.local.LocalClient(p)
    return c.info()['commit_revision']


def get_path_repository(p):
    """
    Get the VCS repository for the file at path ``p``.

    :param p: path
    :return: The URI for the root of the repository the file is part of.

    """
    c = svn.local.LocalClient(p)
    return c.info()['repository/root']
