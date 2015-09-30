#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Docstring for test_utils_log
"""

from tendril.utils import log
import logging


def test_log_default():
    logger = log.get_logger("Default_Logger", log.DEFAULT)
    assert logger.name == "Default_Logger"
    assert logger.level == log.DEFAULT

    logger = log.get_logger("SP_Default_Logger", log.DEFAULT)
    assert logger.name == "SP_Default_Logger"
    assert logger.level == log.DEFAULT


def test_log_other():
    logger = log.get_logger("Critical_Logger", log.CRITICAL)
    assert logger.name == "Critical_Logger"
    assert logger.level == logging.CRITICAL

    logger = log.get_logger("Error_Logger", log.ERROR)
    assert logger.name == "Error_Logger"
    assert logger.level == logging.ERROR

    logger = log.get_logger("Warning_Logger", log.WARNING)
    assert logger.name == "Warning_Logger"
    assert logger.level == logging.WARNING

    logger = log.get_logger("Info_Logger", log.INFO)
    assert logger.name == "Info_Logger"
    assert logger.level == logging.INFO

    logger = log.get_logger("Debug_Logger", log.DEBUG)
    assert logger.name == "Debug_Logger"
    assert logger.level == logging.DEBUG
