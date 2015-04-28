"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import entityhub.projects
import dox.gedaproject


for project in entityhub.projects.projects:
    dox.gedaproject.generate_docs(entityhub.projects.projects[project])
