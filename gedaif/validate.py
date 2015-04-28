"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.INFO)

import gedaif.projfile
import gedaif.gsymlib

import boms.electronics

from gedaif.conffile import NoGedaProjectException


def check(projectfolder):
    logger.info("Attempting to Validate Project at : " + projectfolder)
    try:
        gpf = gedaif.projfile.GedaProjectFile(projectfolder)
    except NoGedaProjectException:
        logger.critical("Configs file missing. No further validation will be attempted")
        return False

    logger.debug("Config and Project File loaded. Proceeding with Validation")

    configs = []
    for config in gpf.configsfile.configdata['configurations']:
        configs.append(config['configname'])

    logger.info("Found " + str(len(configs)) + " Configurations.")
    logger.debug("Creating Electronics BOM")
    bom = boms.electronics.import_pcb(projectfolder)

    for config in configs:
        logger.info("Validating Configuration : " + config)
        logger.debug("Creating Output BOM for Configuration : " + config)
        obom = bom.create_output_bom(config)
        logger.debug("Checking Components for Configuration : " + config)
        for line in obom.lines:
            ident = line.ident
            if not gedaif.gsymlib.is_recognized(ident) and not ident.startswith('PCB '):
                logger.warning("Component not recognized by gsymlib : " + line.ident + " " + str(line.refdeslist))
            elif not ident.startswith('PCB '):
                symbol = gedaif.gsymlib.get_symbol(line.ident)
                if symbol.status == "Deprecated":
                    logger.warning("Component or Symbol used is Deprecated : " + line.ident + " " + str(line.refdeslist))
        logger.info("Validation Complete for Configuration : " + config)
