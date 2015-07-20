"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL  # noqa

DEFAULT = logging.INFO


def init():
    logging.basicConfig(level=logging.DEBUG)


def get_logger(name, level):
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(DEFAULT)
    return logger


init()
