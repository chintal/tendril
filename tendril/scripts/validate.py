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
Project Validation Script  (``tendril-validate``)
=================================================

Reports validation errors for the specified projects / modules.

.. seealso::
    :mod:`tendril.boms.validate`

.. rubric:: Script Usage

.. argparse::
    :module: tendril.scripts.validate
    :func: _get_parser
    :prog: tendril-validate
    :nodefault:

"""

import os
import argparse

from tendril.gedaif import conffile
from tendril.entityhub import projects
from tendril.entityhub import modules
from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.fsutils import in_directory

from .helpers import add_module_selector_options
from .helpers import get_project_folder
from .helpers import add_base_options

from tendril.utils import log
logger = log.get_logger("validate", log.DEFAULT)


def _get_parser():
    """
    Constructs the CLI argument parser for the tendril-validate script.
    """
    parser = argparse.ArgumentParser(
        description='Validate (gEDA) projects and modules.',
        prog='tendril-validate'
    )
    add_base_options(parser)
    add_module_selector_options(parser)
    parser.add_argument(
        '--sourcing', '-s', action='store_true', default=False,
        help='Report sourcing errors as well.'
    )
    return parser


def validate_module(modulename, s=False, statuses=None):
    """
    Report validation errors for the specified module.
    :param modulename: The name of the module.
    :param s: Whether to report sourcing errors as well.
    :param statuses: Criterion for module status to include the module.
    """
    module = modules.get_module_prototype(modulename)
    if statuses is not None:
        if module.status not in statuses:
            return
    logger.info("VALIDATING MODULE {0}".format(modulename))
    module.validation_errors.render_cli(modulename)
    if s is True:
        module.sourcing_errors.render_cli(modulename + ' SOURCING')


def validate_project(projectfolder, s=False, statuses=None):
    """
    Report validation errors for all modules provided by the specified project.
    :param projectfolder: The path to the project folder.
    :param s: Whether to report sourcing errors as well.
    :param statuses: Criterion for module status to include the module.
    """
    try:
        projectfolder = get_project_folder(projectfolder)
        cf = conffile.ConfigsFile(projectfolder)
        modulenames = cf.configuration_names
        for modulename in modulenames:
            validate_module(modulename, s=s, statuses=statuses)
    except conffile.NoGedaProjectError:
        logger.error("No gEDA Project found at " + projectfolder)


def validate_all(s=False, statuses=None):
    """
    Report validation errors for all known modules.
    :param s: Whether to report sourcing errors as well.
    :param statuses: Criterion for module status to include the module.
    """
    for project, projectfolder in projects.projects.items():
        validate_project(projectfolder, s=s, statuses=statuses)


def main():
    """
    The tendril-validate script entry point.
    """
    import logging
    logging.getLogger('tendril.sourcing.electronics').setLevel(logging.WARNING)
    logging.getLogger('tendril.utils.www').setLevel(logging.WARNING)
    parser = _get_parser()
    args = parser.parse_args()
    statuses = args.statuses or []
    statuses.extend(['Active', 'Prototype', 'Prospective', 'Experimental'])
    if args.all:
        validate_all(s=args.sourcing, statuses=statuses)
    else:
        done = False
        if args.modules:
            for modulename in args.modules:
                validate_module(modulename, s=args.sourcing)
                done = True
        else:
            for projfolder in args.projfolders:
                if not os.path.isabs(projfolder):
                    projfolder = os.path.join(os.getcwd(), projfolder)
                    projfolder = os.path.normpath(projfolder)
                if not in_directory(projfolder, PROJECTS_ROOT):
                    logger.error(
                        'Provided directory does not seem to be under the '
                        'tendril PROJECTS_ROOT. Skipp   ing ' + projfolder
                    )
                    continue
                targets = [projfolder]
                if args.recurse:
                    lprojects, lpcbs, lcards, lcard_reporoot, lcable_projects = \
                        projects.get_projects(projfolder)
                    targets.extend([lprojects[x] for x in lprojects.keys()])
                for target in targets:
                    validate_project(target, s=args.sourcing, statuses=statuses)
        if not done:
            parser.print_help()


if __name__ == '__main__':
    main()
