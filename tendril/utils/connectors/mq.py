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
import atexit
import threading
from contextlib import contextmanager

from tendril.utils.config import MQ_SERVER
from tendril.utils.config import MQ_SERVER_PORT
from tendril.utils.config import ENABLE_THREADED_CONNECTORS

from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)


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
        pika.ConnectionParameters(MQ_SERVER, MQ_SERVER_PORT,
                                  heartbeat_interval=1200)
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


def mq_subscribe(channel, exchange, callback):
    logger.debug("Subscribing to channel : {0}".format(exchange))
    result = channel.queue_declare(exclusive=True)
    channel.queue_bind(exchange=exchange,
                       queue=result.method.queue)
    channel.basic_consume(callback,
                          queue=result.method.queue)


class EventMonitor(threading.Thread):
    def __init__(self, exchange, callback):
        self._exchange = exchange
        self._callback = callback
        self.stop_requested = threading.Event()
        threading.Thread.__init__(self)

    def run(self):
        self._run()

    def _run(self):
        logger.debug("Starting Event Monitor : {0}".format(self._exchange))
        with mq_connection() as connection:
            channel = connection.channel()
            channel.exchange_declare(exchange=self._exchange,
                                     exchange_type='fanout')

            def _manager():
                if self.stop_requested.isSet():
                    logger.debug(
                        "Stopping Event Monitor : {0}".format(self._exchange))
                    channel.stop_consuming()
                    connection.close()
                else:
                    connection.add_timeout(1, _manager)

            def _cb(ch, method, properties, body):
                logger.debug(" [x] Received %r" % body)
                self._callback(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            connection.add_timeout(1, _manager)
            mq_subscribe(channel, self._exchange, _cb)
            channel.start_consuming()

    def stop(self):
        self.stop_requested.set()
        self.join()

    def handle_events(self):
        pass


_monitors = {}


def monitor_start(exchange, callback):
    if not ENABLE_THREADED_CONNECTORS:
        raise MQServerNotConfigured("Threaded connectors not enabled.")
    global _monitors
    if exchange not in _monitors.keys():
        _monitors[exchange] = EventMonitor(exchange, callback)
        _monitors[exchange].setDaemon(True)
        _monitors[exchange].start()
        atexit.register(monitor_stop, exchange)
    else:
        raise Exception("Monitor already running")


def monitor_stop(exchange):
    global _monitors
    if exchange not in _monitors.keys():
        raise Exception("Monitor not running, cannot stop.")
    else:
        _monitors[exchange].stop()
        _monitors.pop(exchange)
