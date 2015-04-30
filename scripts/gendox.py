"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.DEFAULT)
import entityhub.projects
import dox.gedaproject


for project in entityhub.projects.projects:
    logger.info("Checking " + project + " for changes and updating documentation")
    dox.gedaproject.generate_docs(entityhub.projects.projects[project])
