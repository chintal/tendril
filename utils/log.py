"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

"""
This file is part of qicada
See the COPYING, README, and INSTALL files for more information
"""

import sys

from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import logging

DEFAULT = INFO


def init():
    logging.basicConfig(level=logging.DEBUG)
    # observer = log.PythonLoggingObserver()
    # observer.start()


def get_logger(name, level):
    # logger = Logger(name)
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(DEFAULT)
    return logger


# class Logger(object):
#     def __init__(self, name):
#         self._logger = log.msg
#         self._name = name
#         self._level = WARNING
#
#     def info(self, msg):
#         if INFO >= self._level:
#             self._logger(self._name + ' ::I: ' + msg, logLevel=INFO)
#
#     def debug(self, msg):
#         if DEBUG >= self._level:
#             self._logger(self._name + ' ::DBG: ' + msg, logLevel=DEBUG)
#
#     def warning(self, msg):
#         if WARNING >= self._level:
#             self._logger(self._name + ' ::WARN: ' + msg, logLevel=WARNING)
#
#     def error(self, msg):
#         if ERROR >= self._level:
#             self._logger(self._name + ' ::ERROR: ' + msg, logLevel=ERROR)
#
#     def critical(self, msg):
#         if CRITICAL >= self._level:
#             self._logger(self._name + ' ::CRITICAL: ' + msg, logLevel=CRITICAL)
#
#     def setLevel(self, level):
#         self._level = level


# class Logger(object):
#     def __init__(self, name):
#         self._logger = logging.getLogger(name)
#
#     def info(self, msg):
#         self._logger.info(msg)
#
#     def debug(self, msg):
#         self._logger.debug(msg)
#
#     def warning(self, msg):
#         self._logger.warning(msg)
#
#     def error(self, msg):
#         self._logger.error(msg)
#
#     def critical(self, msg, *args, **kwargs):
#         self._logger.critical(msg, args, kwargs)
#
#     def setLevel(self, level):
#         self._logger.setLevel(level)
