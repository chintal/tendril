"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEFAULT)
from koala.entityhub import projects
from koala.dox import gedaproject


for project in projects.projects:
    logger.info("Checking " + project + " for changes and updating documentation")
    gedaproject.generate_docs(projects.projects[project])
