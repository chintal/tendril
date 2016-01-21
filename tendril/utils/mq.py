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
Docstring for mq
"""


import xmlrpclib
import atexit
import uuid


from tendril.utils.config import MQ_SERVER


def _connect_to_mq_server():
    s = xmlrpclib.Server(MQ_SERVER + '/control')
    return s

mq_server = _connect_to_mq_server()
owned_keys = []


def create_mq(key=None):
    if key is None:
        key = uuid.uuid4()
    mq_server.create_mq(key)
    owned_keys.append(key)
    return key


def publish(key, data):
    mq_server.publish(key, data)
    owned_keys.append(key)


def delete_mq(key):
    mq_server.delete_mq(key)
    owned_keys.append(key)


def cleanup():
    for key in owned_keys:
        delete_mq(key)

atexit.register(cleanup)
