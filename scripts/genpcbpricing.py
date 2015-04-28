"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import entityhub.projects
import sourcing.csil


for project in entityhub.projects.projects:
    sourcing.csil.generate_pcb_pricing(entityhub.projects.projects[project])
