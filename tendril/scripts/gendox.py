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
Project Documentation Generation Script (``tendril-gendox``)
============================================================

This script (re-)generates all the documentation linked to recognized
projects based on the criteria specified by the command parameters.

.. seealso::
    :mod:`tendril.dox.gedaproject`

.. rubric:: Output Folders

The underlying functions generate the docs in the folder specified by the
``REFDOC_ROOT`` configuration option from :mod:`tendril.utils.config`. This
folder may be configured by your instance's ``instance_config.py`` file to
point to a remote filesystem.

If you would like to generate the documentation on your local filesystem
instead, you should override the instance's ``REFDOC_ROOT`` configuration
parameter by setting it to a folder on your local filesystem in your
``local_config_overrides.py`` file.

.. warning::
    It is strongly recommended to have this folder outside of
    the normal project tree, in order to prevent the generated documentation
    (which is mostly in binary file formats) from littering your VCS working
    folders.

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.gendox
    :func: _get_parser
    :prog: tendril-gendox
    :nodefault:

"""

import os
import argparse

from tendril.gedaif.conffile import NoGedaProjectError
from tendril.gedaif import conffile
from tendril.entityhub import projects
from tendril.dox import gedaproject
from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.fsutils import in_directory

from .helpers import add_project_selector_options
from .helpers import add_base_options

from tendril.utils import log
logger = log.get_logger("gendox", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-gendox script.
    """
    parser = argparse.ArgumentParser(
        description='(Re-)Generate gEDA project documentation.',
        prog='tendril-gendox'
    )
    add_base_options(parser)
    parser.add_argument(
        '--force', '-f', action='store_true', default=False,
        help='Regenerate documentation even if it seems to be up-to-date'
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true', default=False,
        help="Dry run only. Don't do anything which can change the filesystem"
    )

    add_project_selector_options(parser)
    return parser


def regenerate_all(force=False, dry_run=False):
    """
    Regenerates documentation for all projects

    :param force: Regenerate even for up-to-date projects.
    :param dry_run: Check only. Don't actually generate any documentation.

    """
    for project in projects.projects:
        if dry_run:
            conffile.ConfigsFile(projects.projects[project])
            logger.info("Will check " + projects.projects[project])
        else:
            logger.info("Checking " + projects.projects[project])
            gedaproject.generate_docs(projects.projects[project], force=force)


def main():
    """
    The tendril-gendox script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    force = args.force
    if args.all:
        regenerate_all(force=force, dry_run=args.dry_run)
    else:
        if not len(args.projfolders):
            parser.print_help()
        for projfolder in args.projfolders:
            if not os.path.isabs(projfolder):
                projfolder = os.path.join(os.getcwd(), projfolder)
                projfolder = os.path.normpath(projfolder)
            if not in_directory(projfolder, PROJECTS_ROOT):
                logger.error(
                    'Provided directory does not seem to be under the '
                    'tendril PROJECTS_ROOT. Skipping ' + projfolder
                )
                continue
            targets = [projfolder]
            if args.recurse:
                lprojects, lpcbs, lcards, lcard_reporoot = \
                    projects.get_projects(projfolder)
                targets.extend([lprojects[x] for x in lprojects.keys()])
            for target in targets:
                try:
                    if args.dry_run is False:
                        gedaproject.generate_docs(target, force=force)
                        logger.info("Checked " + target)
                    else:
                        conffile.ConfigsFile(target)
                        logger.info("Will check " + target)
                except NoGedaProjectError:
                    # Make a guess.
                    if os.path.split(target)[1] == 'configs.yaml':
                        target == os.path.split(target)[0]
                    if os.path.split(target)[1] == 'schematic':
                        target == os.path.split(target)[0]
                    try:
                        if args.dry_run is False:
                            gedaproject.generate_docs(target, force=force)
                            logger.info("Checked " + target)
                        else:
                            conffile.ConfigsFile(target)
                            logger.info("Will check " + target)
                    except NoGedaProjectError:
                        logger.error("No gEDA Project found at " + target)


if __name__ == '__main__':
    main()
