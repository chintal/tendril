#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
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
Docstring for warmup
"""

import timeit
from tendril.utils import log
logger = log.get_logger(__name__, level=log.DEFAULT)


def warm_up_caches():
    start_time = timeit.default_timer()
    logger.info("Starting Warmup Cycle")
    logger.info("Warming up gedaif.gsymlib")
    from tendril.gedaif import gsymlib
    logger.info("Warming up sourcing.electronics")
    from tendril.sourcing import electronics
    logger.info("Warming up entityhub.directory")
    from tendril.entityhub import directory
    logger.info("Warming up entityhub.modules")
    from tendril.entityhub import modules
    logger.info("Warming up entityhub.products")
    from tendril.entityhub import products
    logger.info("Warming up entityhub.supersets")
    from tendril.entityhub import supersets
    logger.info("Warming up inventory.electronics")
    from tendril.inventory import electronics
    elapsed = timeit.default_timer() - start_time
    logger.info("Finished Warmup Cycle.")
    logger.info("Warmup took {0} seconds.".format(elapsed))
