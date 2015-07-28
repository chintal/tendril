"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import koala.gedaif.validate
import koala.entityhub.projects


for project in koala.entityhub.projects.projects:
    koala.gedaif.validate.check(koala.entityhub.projects.projects[project])
