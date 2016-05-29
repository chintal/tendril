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
Docstring for mouser
"""


from suds.sax.element import Element

from tendril.utils import www
from tendril.utils import log

from .vendors import VendorBase
from .vendors import VendorElnPartBase

logger = log.get_logger(__name__, log.DEFAULT)


class MouserElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        super(MouserElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
        c = self._vendor.api_client
        pass


class VendorEPass(VendorBase):
    _partclass = MouserElnPart

    #: Supported Device Classes
    #:
    #: .. hint::
    #:      This handles instance-specific tweaks, and should be
    #:      modified to match your instance's nomenclature guidelines.
    #:
    _devices = [
        'IC SMD', 'IC THRU', 'IC PLCC',
        # 'FERRITE BEAD SMD', 'TRANSISTOR THRU', 'TRANSISTOR SMD',
        # 'CONN DF13', 'CONN DF13 HOUS', 'CONN DF13 WIRE', 'CONN DF13 CRIMP',
        # 'CONN MODULAR', 'DIODE SMD', 'DIODE THRU', 'BRIDGE RECTIFIER',
        # 'VARISTOR', 'RES SMD', 'RES THRU', 'RES ARRAY SMD',
        # 'CAP CER SMD', 'CAP TANT SMD', 'CAP AL SMD', 'CAP MICA SMD',
        # 'TRANSFORMER SMD', 'INDUCTOR SMD',
        # 'CRYSTAL AT', 'CRYSTAL OSC', 'CRYSTAL VCXO'
    ]

    _type = 'Mouser SOAP API'

    # TODO This is vendor specific, and should probably come from the config
    _url_base = 'http://www.mouser.com/'
    _api_endpoint = 'http://www.mouser.in/service/searchapi.asmx?WSDL'

    def __init__(self, apikey=None, **kwargs):
        self._api_key = apikey
        self._client = self._build_api_client()
        super(VendorEPass, self).__init__(**kwargs)

    def _build_mouser_header(self):
        header_partnerid = Element('PartnerID').setText(self._api_key)
        header_accountinfo = Element('AccountInfo')
        header_accountinfo.insert(header_partnerid)
        header = Element('MouserHeader')
        header.insert(header_accountinfo)
        header.set('xmlns', 'http://api.mouser.com/service')
        return header

    def _build_api_client(self):
        c = www.get_soap_client(self._api_endpoint)
        header = self._build_mouser_header()
        c.set_options(soapheaders=header)
        c.set_options(prefixes=False)
        c.set_options(service='SearchAPI', port='SearchAPISoap12')
        return c

    def api_client(self):
        return self._client

    def search_vpnos(self, ident):
        return None, 'NOAPIKEY'
