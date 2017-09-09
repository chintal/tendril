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
The Prefab Server Connector Module (:mod:`tendril.utils.connectors.prefab`)
===========================================================================

"""

import json
import jsonpickle
import requests
import requests.exceptions

from tendril.utils.config import PREFAB_SERVER
from tendril.utils.config import USE_PREFAB_SERVER


class PrefabServerUnavailable(Exception):
    pass


def rpc(method, **kwargs):
    if not USE_PREFAB_SERVER:
        raise PrefabServerUnavailable
    headers = {'content-type': 'application/json'}
    payload = {
        "method": method, "params": kwargs,
        "jsonrpc": "2.0", 'id': '1'
    }
    try:
        response = requests.post(PREFAB_SERVER,
                                 data=json.dumps(payload),
                                 headers=headers,
                                 timeout=(0.1, 5)).json()
    except requests.ConnectionError:
        raise PrefabServerUnavailable
    except requests.exceptions.ReadTimeout:
        raise PrefabServerUnavailable
    if 'result' not in response.keys():
        return {}
    return jsonpickle.decode(response['result'])
