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
import argparse

from tendril.gedaif.conffile import NoGedaProjectException
from tendril.entityhub import projects
from tendril.dox import gedaproject
from tendril.utils import log
logger = log.get_logger("gendox", log.DEFAULT)


def regenerate_all(force=False):
    for project in projects.projects:
        logger.info("Checking " + project)
        gedaproject.generate_docs(projects.projects[project], force=force)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='(Re-)Generate gEDA project documentation.',
        prog='python -m tendril.scripts.gendox'
    )
    parser.add_argument(
        'projfolders', metavar='PATH', type=str, nargs='*',
        help='gEDA Project Folder(s), or leave empty for all'
    )
    parser.add_argument(
        '--force', action='store_true', default=False,
        help='Regenerate documentation even if it seems to be up-to-date'
    )
    parser.add_argument(
        '--all', '-a', action='store_true', default=False,
        help='Regenerate documentation for all projects'
    )

    args = parser.parse_args()
    force = args.force
    if args.all:
        regenerate_all(force=force)
    else:
        if not len(args.projfolders):
            parser.print_help()
        for projfolder in args.projfolders:
            if not os.path.isabs(projfolder):
                projfolder = os.path.join(os.getcwd(), projfolder)
                projfolder = os.path.normpath(projfolder)
            try:
                gedaproject.generate_docs(projfolder, force=force)
                logger.info("Checked " + projfolder)
            except NoGedaProjectException:
                # Make a guess.
                if os.path.split(projfolder)[1] == 'configs.yaml':
                    projfolder == os.path.split(projfolder)[0]
                if os.path.split(projfolder)[1] == 'schematic':
                    projfolder == os.path.split(projfolder)[0]
                try:
                    gedaproject.generate_docs(projfolder, force=force)
                    logger.info("Checked " + projfolder)
                except NoGedaProjectException:
                    logger.error("No gEDA Project found at " + projfolder)
