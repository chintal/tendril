#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2017 Chintalagiri Shashank
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
Docstring for maintenance
"""


import json
from tendril.connectors.mq import mq_publish
from tendril.connectors.mq import mq_connection
from tendril.connectors.mq import MQServerUnavailable


def update_vpinfo(vendor, ident, vpno):
    try:
        with mq_connection() as connection:
            channel = connection.channel()
            message = json.dumps({'vendor': vendor,
                                  'ident': ident,
                                  'vpno': vpno})
            mq_publish(channel, 'maintenance_vendor_vpinfo', message)
    except MQServerUnavailable:
        return


def update_vpmap(vendor, ident):
    try:
        with mq_connection() as connection:
            channel = connection.channel()
            message = json.dumps({'vendor': vendor,
                                  'ident': ident})
            mq_publish(channel, 'maintenance_vendor_vpmap', message)
    except MQServerUnavailable:
        return
