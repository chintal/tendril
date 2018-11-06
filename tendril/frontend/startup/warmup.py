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
logger = log.get_logger(__name__, level=log.INFO)


def warm_up_caches():
    start_time = timeit.default_timer()
    logger.info("Starting Warmup Cycle")

    warmup_times = []

    logger.info("Warming up gedaif.gsymlib")
    l_start_time = timeit.default_timer()
    from tendril.gedaif import gsymlib
    warmup_times.append(('gedaif.gsymlib', timeit.default_timer() - l_start_time))

    logger.info("Warming up sourcing.electronics")
    l_start_time = timeit.default_timer()
    from tendril.sourcing import electronics
    warmup_times.append(('sourcing.electronics', timeit.default_timer() - l_start_time))

    logger.info("Warming up entityhub.directory")
    l_start_time = timeit.default_timer()
    from tendril.entityhub import directory
    warmup_times.append(('entityhub.directory', timeit.default_timer() - l_start_time))

    logger.info("Warming up entityhub.modules")
    l_start_time = timeit.default_timer()
    from tendril.entityhub import modules
    warmup_times.append(('entityhub.modules', timeit.default_timer() - l_start_time))

    logger.info("Warming up entityhub.products")
    l_start_time = timeit.default_timer()
    from tendril.entityhub import products
    warmup_times.append(('entityhub.products', timeit.default_timer() - l_start_time))

    logger.info("Warming up entityhub.supersets")
    l_start_time = timeit.default_timer()
    from tendril.entityhub import supersets
    warmup_times.append(('entityhub.supersets', timeit.default_timer() - l_start_time))

    logger.info("Warming up inventory.electronics")
    l_start_time = timeit.default_timer()
    from tendril.inventory import electronics
    warmup_times.append(('inventory.electronics', timeit.default_timer() - l_start_time))

    elapsed = timeit.default_timer() - start_time
    logger.info("Finished Warmup Cycle.")
    logger.info("Warmup took {0} seconds.".format(elapsed))
    for k, t in warmup_times:
        logger.info('{0:25} : {1:>5.1f} seconds'.format(k, t))
