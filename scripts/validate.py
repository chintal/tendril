"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import gedaif.validate
import entityhub.projects


for project in entityhub.projects.projects:
    gedaif.validate.check(entityhub.projects.projects[project])
