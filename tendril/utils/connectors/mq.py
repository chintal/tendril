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
Docstring for mq
"""

import pika
from contextlib import contextmanager

from tendril.utils.config import MQ_SERVER
from tendril.utils.config import MQ_SERVER_PORT


class MQServerUnavailable(Exception):
    pass


class MQServerNotResponding(MQServerUnavailable):
    pass


class MQServerNotConfigured(MQServerUnavailable):
    pass


@contextmanager
def mq_connection():
    if not MQ_SERVER:
        raise MQServerNotConfigured
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(MQ_SERVER, MQ_SERVER_PORT)
    )
    try:
        yield connection
    except:
        raise
    finally:
        connection.close()


def mq_publish(channel, key, message):
    channel.queue_declare(queue=key, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=key,
                          body=message,
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          ))
