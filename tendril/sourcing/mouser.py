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
Mouser Vendor Module (:mod:`tendril.sourcing.mouser`)
=====================================================

"""

import traceback
import re
from suds.sax.element import Element

from tendril.conventions.electronics import check_for_std_val
from tendril.conventions.electronics import parse_ident
from tendril.utils import www
from tendril.utils import log

from .vendors import VendorBase
from .vendors import VendorElnPartBase
from .vendors import VendorPrice
from .vendors import SearchPart
from .vendors import SearchResult

logger = log.get_logger(__name__, log.DEFAULT)


class MouserElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        super(MouserElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
        c = self._vendor.api_client
        r = c.service.SearchByPartNumber(mouserPartNumber=self.vpno)
        if not r.NumberOfResult:
            raise ValueError(
                'Unable to retrieve part information for part number.'
            )

        part_data = None
        for part in r.Parts[0]:
            if part.MouserPartNumber == self.vpno:
                part_data = part

        if not part_data:
            raise ValueError(
                'Unable to retrieve part information for part number.'
            )

        self._load_from_response(part_data)

    def _load_from_response(self, part_data):
        self.manufacturer = part_data.Manufacturer
        self.mpartno = part_data.ManufacturerPartNumber
        self.datasheet = part_data.DataSheetUrl
        self.package = None
        self.vqtyavail = int(part_data.Availability.split()[0])
        self.vpartdesc = part_data.Description
        self.vparturl = part_data.ProductDetailUrl

        for price in part_data.PriceBreaks[0]:
            self.add_price(VendorPrice(
                price.Quantity,
                float(re.findall(r'\d+\.*\d*', price.Price)[0]),
                self._vendor.currency)
            )

    def load_from_response(self, response):
        self._load_from_response(part_data=response)


class VendorMouser(VendorBase):
    _partclass = MouserElnPart

    #: Supported Device Classes
    #:
    #: .. hint::
    #:      This handles instance-specific tweaks, and should be
    #:      modified to match your instance's nomenclature guidelines.
    #:
    _devices = [
        'IC SMD', 'IC THRU', 'IC PLCC',
        'FERRITE BEAD SMD', 'TRANSISTOR THRU', 'TRANSISTOR SMD',
        'CONN DF13', 'CONN DF13 HOUS', 'CONN DF13 WIRE', 'CONN DF13 CRIMP',
        'CONN MODULAR', 'DIODE SMD', 'DIODE THRU', 'BRIDGE RECTIFIER',
        'VARISTOR', 'RES SMD', 'RES THRU',  # 'RES ARRAY SMD',
        'CAP CER SMD', 'CAP AL SMD', 'CAP MICA SMD',  # 'CAP TANT SMD',
        'TRANSFORMER SMD', 'INDUCTOR SMD', 'RELAY',
        'CRYSTAL AT', 'CRYSTAL OSC', 'CRYSTAL VCXO', 'ZENER SMD'
    ]

    _type = 'Mouser SOAP API'

    _url_base = 'http://www.mouser.com/'
    _api_endpoint = 'http://www.mouser.in/service/searchapi.asmx?WSDL'

    def __init__(self, apikey=None, **kwargs):
        self._api_key = apikey
        self._client = self._build_api_client()
        super(VendorMouser, self).__init__(**kwargs)
        self.add_order_additional_cost_component("Customs", 12.85)

    def _build_mouser_header(self):
        header_partnerid = Element('PartnerID').setText(self._api_key)
        header_accountinfo = Element('AccountInfo')
        header_accountinfo.insert(header_partnerid)
        header = Element('MouserHeader')
        header.insert(header_accountinfo)
        header.set('xmlns', 'http://api.mouser.com/service')
        return header

    def _build_api_client(self):
        c = www.get_soap_client(self._api_endpoint,
                                cache_requests=True,
                                max_age=600000,
                                minimum_spacing=5)
        header = self._build_mouser_header()
        c.set_options(soapheaders=header)
        c.set_options(prefixes=False)
        c.set_options(service='SearchAPI', port='SearchAPISoap12')
        return c

    @property
    def api_client(self):
        return self._client

    def search_vpnos(self, ident):
        parts, strategy = self._search_vpnos(ident)
        if parts is None:
            return parts, strategy

        for part in parts:
            partobj = self._partclass(part.pno, ident=ident,
                                      vendor=self, max_age=None,
                                      shell_only=True)
            partobj.load_from_response(part.raw)
            partobj.commit()

        pnos = [x.pno for x in parts]
        return pnos, strategy

    def _search_vpnos(self, ident):
        device, value, footprint = parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if device.startswith('RES') or device.startswith('POT') or \
                    device.startswith('CAP') or device.startswith('CRYSTAL'):
                if check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value, footprint)
                try:
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint)
            else:
                return None, 'FILTER_NODEVICE'
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    @staticmethod
    def _process_response_part(rpart):
        ns = True
        try:
            if int(rpart.Availability.split()[0]) > 0:
                ns = False
        except:
            pass
        return SearchPart(pno=rpart.MouserPartNumber,
                          mfgpno=rpart.ManufacturerPartNumber,
                          package=rpart.Category, ns=ns, unitp=None,
                          minqty=rpart.Min, raw=rpart
                          )

    @staticmethod
    def _get_device_catstrings(device):
        if device.startswith('DIODE'):
            catstrings = ['Rectifiers',
                          'Schottky Diodes & Rectifiers',
                          'Diodes - General Purpose, Power, Switching',
                          'TVS Diodes',
                          ]
        elif device.startswith('ZENER'):
            catstrings = ['Zener Diodes',]
        elif device.startswith('TRANSISTOR'):
            catstrings = ['Bipolar Transistors - BJT',
                          'Bipolar Transistors - Pre-Biased',
                          'Darlington Transistors',
                          'MOSFET',
                          'JFET']
        else:
            return False, None
        return True, catstrings

    def _filter_results_by_category(self, parts, device):
        r, catstrings = self._get_device_catstrings(device)
        if not r:
            return SearchResult(True, parts, 'UNFILTERED')
        parts = [x for x in parts if x.package in catstrings]
        return SearchResult(True, parts, 'CATFILTER')

    def _get_search_vpnos(self, device, value, footprint):
        # TODO Allow non-stocked parts and filter them later?
        r = self.api_client.service.SearchByKeyword(
            keyword=value, records=50, startingRecord=0, searchOptions=4
        )

        nresults = r.NumberOfResult
        if not nresults:
            return None, 'NORESULTS'
        rparts = r.Parts[0]
        parts = [self._process_response_part(x) for x in rparts]
        parts = self._remove_duplicates(parts)
        sr = self._filter_results_by_category(parts, device)
        # pnos = [x.pno for x in sr.parts]
        return sr.parts, sr.strategy

    def _get_pas_vpnos(self, device, value, footprint):
        raise NotImplementedError
