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
PCB Pricing Generation Script (``tendril-genpcbpricing``)
=========================================================

This script (re-)generates pcb pricing information for PCBs linked to
recognized projects based on the criteria specified by the command parameters.

.. hint::
    The parameters used for obtaining the PCB pricing and the quantity range
    are determined by the content of the project's ``configs.yaml`` file.

.. warning::
    This script retrieves pricing information from the PCB vendor. It will
    take quite some time to execute.

.. seealso::
    :mod:`tendril.sourcing.csil`
    :func:`tendril.sourcing.csil.generate_pcb_pricing`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.genpcbpricing
    :func: _get_parser
    :prog: tendril-genpcbpricing
    :nodefault:

.. todo::
    Generalize this process and remove vendor specificity.

"""

import os
import argparse

from tendril.entityhub import projects
from tendril.sourcing import csil

from tendril.gedaif.conffile import NoGedaProjectError
from tendril.gedaif import conffile

from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.fsutils import in_directory

from .helpers import add_project_selector_options
from .helpers import add_base_options

from tendril.utils import log
logger = log.get_logger("genpcbpricing", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-genpcbpricing script.
    """
    parser = argparse.ArgumentParser(
        description='(Re-)Generate CSIL PCB Pricing Information.',
        prog='tendril-genpcbpricing'
    )
    add_base_options(parser)
    parser.add_argument(
        '--force', '-f', action='store_true', default=False,
        help='Regenerate pricing even if it seems to be up-to-date'
    )
    parser.add_argument(
        '--lazy', '-l', action='store_true', default=False,
        help="Don't regenerate pricing if it exists, even if it "
             "seems to be out-of-date"
    )
    parser.add_argument(
        '--dry-run', '-n', action='store_true', default=False,
        help="Dry run only. Don't do anything which can change the filesystem"
    )

    add_project_selector_options(parser)
    return parser


def regenerate_all(force=False, lazy=False, dry_run=False):
    """
    Regenerates PCB pricing information for all projects.

    :param force: Regenerate even for up-to-date projects.
    :param lazy: New projects only. Doesn't regenerate for projects with
                 out-of-date pricing information
    :param dry_run: Check only. Don't actually generate any documentation.

    """
    for project in projects.pcbs:
        if dry_run:
            conffile.ConfigsFile(projects.pcbs[project])
            logger.info("Will check " + projects.pcbs[project])
        else:
            logger.info("Checking " + projects.pcbs[project])
            csil.generate_pcb_pricing(projects.pcbs[project],
                                      forceregen=force, noregen=lazy)


def main():
    """
    The tendril-genpcbpricing script entry point.
    """
    parser = _get_parser()
    args = parser.parse_args()
    force = args.force
    lazy = args.lazy
    if args.all:
        regenerate_all(force=force, lazy=lazy, dry_run=args.dry_run)
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
                targets.extend([lpcbs[x] for x in lpcbs.keys()])
            for target in targets:
                try:
                    if args.dry_run is False:
                        csil.generate_pcb_pricing(
                            target, forceregen=force, noregen=lazy
                        )
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
                            csil.generate_pcb_pricing(
                                target, forceregen=force, noregen=lazy
                            )
                            logger.info("Checked " + target)
                        else:
                            conffile.ConfigsFile(target)
                            logger.info("Will check " + target)
                    except NoGedaProjectError:
                        logger.error("No gEDA Project found at " + target)


if __name__ == '__main__':
    main()
