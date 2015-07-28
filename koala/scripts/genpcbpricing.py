"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.entityhub import projects
from koala.sourcing  import csil


def generate():
    for project in projects.projects:
        csil.generate_pcb_pricing(projects.projects[project])


def flushpcbpricing():
    for projectf in projects.projects:
        csil.flush_pcb_pricing(projects.projects[projectf])


if __name__ == '__main__':
    generate()
