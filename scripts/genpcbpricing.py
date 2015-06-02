"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import entityhub.projects
import sourcing.csil


def generate():
    for project in entityhub.projects.projects:
        sourcing.csil.generate_pcb_pricing(entityhub.projects.projects[project])


def flushpcbpricing():
    for projectf in entityhub.projects.projects:
        sourcing.csil.flush_pcb_pricing(entityhub.projects.projects[projectf])


if __name__ == '__main__':
    generate()
