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
Arrow Vendor Module (:mod:`tendril.sourcing.arrow`)
===================================================

'Standalone' Usage
------------------

This module can be imported by itself to provide limited but potentially
useful functionality.

>>> from sourcing.vendors import arrow

.. rubric:: Search

Search for Arrow part numbers given a Tendril-compatible ident string :

>>> arrow.dvobj.search_vpnos('IC SMD W5300 LQFP100-14')
([950-W5300], 'CATFILTER')

Note that only certain types of components are supported by the search. The
``device`` component of the ident string is used to determine whether or not
a search will even be attempted. See :data:`VendorArrow._devices` for a
list of supported device classes. For all device classes, search is
supported only for components whose ``value`` is a manufacturer part number,
or enough of one to sufficiently identify the part in question.

.. seealso::
    :ref:`symbol-conventions`

.. warning::
    Note that the Mouser API does NOT return packages, and as such filtering
    of search results by package is not done here. Effectively, the
    information contained by the ``footprint`` part of the ``ident`` is not
    used by the Mouser support module.

The Mouser vendor support module provided here does not support search for
jellybean components. While the Mouser API used includes a ``Calculator``
search method, neither the allowed search parameters nor the returned
information include the ``package`` information.

Even with supported device types, remember that this search is nowhere near
bulletproof. The more generic a device and/or its name is, the less likely
it is to work. The intended use for this type of search is in concert with
an organization's engineering policies and an instance administrator who
can make the necessary tweaks to the search algorithms and maintain a low
error rate for component types commonly used within the instance.

.. seealso::
    :func:`VendorMouser._get_device_catstrings`

Tweaks and improvements to the search process are welcome as pull requests
to the tendril github repository, though their inclusion will be predicated
on them causing minimal breakage to what already exists.

.. rubric:: Retrieve

Obtain information for a given Mouser part number :

Unlike the :mod:`digikey` vendor support module, the Mouser support package
does not allow direct instantiation of it's VendorPart class. Instead, the
vendor object must be use to retrieve the part. This is done to improve
caching via the vendor object and minimize activity on the API.

>>> p = arrow.dvobj.get_vpart('950-W5300')
>>> p.manufacturer
WIZnet
>>> p.mpartno
W5300
>>> p.vqtyavail
862
>>> p.datasheet
http://www.mouser.com/ds/2/443/W5300_DS_V131E-586393.pdf
>>> p.vpartdesc
Ethernet ICs HI PERF ENET CONTR TCP/IP+MAC+PHY
>>> print p.package
None

The pricing information is also populated by this time, and can be accessed
though the part object using the interfaces defined in those class definitions.

>>> for b in p._prices:
...     print b
...
<VendorPrice ₹ 379.96 @1(1)>
<VendorPrice ₹ 356.42 @50(1)>
<VendorPrice ₹ 335.57 @100(1)>
<VendorPrice ₹ 316.75 @250(1)>

.. hint::
    By default, the :class:`.vendors.VendorPrice` instances are represented
    by the unit price in the currency defined by the
    :data:`tendril.utils.types.currency.native_currency_defn`.

.. warning::
    The Mouser API only returns the first 4 price breaks, even if Mouser
    actually offers additional price breaks. The results obtained from here
    should be manually verified against the Mouser website if the required
    quantity is greater than the MOQ of the largest price break.

The full content of the API response, parsed by :mod:`suds`, is available
from the part object when the part is constructed from an API response. This
content is NOT present when the part has been reconstructed from the database.

>>> p.part_data
(MouserPart){
   Availability = "862 In Stock"
   DataSheetUrl = "http://www.mouser.com/ds/2/443/W5300_DS_V131E-586393.pdf"
   Description = "Ethernet ICs HI PERF ENET CONTR TCP/IP+MAC+PHY"
   ImagePath = "http://www.mouser.com/images/wiznet/images/W5300_SPL.jpg"
   Category = "Ethernet ICs"
   LeadTime = "28 Days"
   LifecycleStatus = None
   Manufacturer = "WIZnet"
   ManufacturerPartNumber = "W5300"
   Min = "1"
   Mult = "1"
   MouserPartNumber = "950-W5300"
   PriceBreaks =
      (ArrayOfPricebreaks){
         Pricebreaks[] =
            (Pricebreaks){
               Quantity = 1
               Price = "$5.65"
               Currency = "USD"
            },
            (Pricebreaks){
               Quantity = 50
               Price = "$5.30"
               Currency = "USD"
            },
            (Pricebreaks){
               Quantity = 100
               Price = "$4.99"
               Currency = "USD"
            },
            (Pricebreaks){
               Quantity = 250
               Price = "$4.71"
               Currency = "USD"
            },
      }
   ProductDetailUrl = "http://in.mouser.com/Search/ProductDetail.aspx?qs=b%252bXOOdUOuvZOuYHXpl8liw%3d%3d"
   Reeling = False
   ROHSStatus = "RoHS Compliant"
   SuggestedReplacement = None
   MultiSimBlue = 0
 }

"""

import traceback

from tendril.conventions.electronics import check_for_std_val
from tendril.conventions.electronics import parse_ident
from tendril.utils import www
from tendril.utils.db import get_session

from tendril.utils.config import ARROW_API_KEY
from tendril.utils.config import ARROW_API_LOGIN

from .vendorbase import VendorBase
from .vendorbase import VendorElnPartBase
from .vendorbase import VendorPrice
from .vendorbase import SearchPart
from .vendorbase import VendorPartInaccessibleError
from tendril.sourcing.db import controller

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class ArrowElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        super(ArrowElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
        # Arrow doesn't seem to believe in part numbers.
        raise VendorPartInaccessibleError

    def _load_from_response(self, part_data):
        self.manufacturer = part_data['manufacturer']['mfrName']
        self.mpartno = part_data['partNum']
        if part_data['hasDatasheet']:
            self.datasheet = None
        else:
            self.datasheet = None
        self.package = part_data['packageType'] or None
        self.vpartdesc = part_data['desc']
        for resource in part_data['resources']:
            if resource['type'] == 'cloud_part_detail':
                self.vparturl = resource['uri']
                break

        sources = part_data['InvOrg']['sources']
        found_sources = 0
        self.vqtyavail = 0
        mpkgqty = None
        for source in self._vendor.apiresult_filter_sources(sources):
            for sourcepart in source['sourceParts']:
                if 'Prices' not in sourcepart.keys() or \
                        not sourcepart['inStock']:
                    continue
                found_sources += 1
                self.vqtyavail += sourcepart['Availability'][0]['fohQty']

                pkgqty = sourcepart['packSize']
                # TODO oqmultiple in VendorPrice doesn't seem to actually
                # be used.
                if not mpkgqty:
                    mpkgqty = pkgqty
                else:
                    mpkgqty = min([pkgqty, mpkgqty])

                for price in sourcepart['Prices']['resaleList']:
                    p = VendorPrice(price['minQty'], price['price'],
                                    self._vendor.currency,
                                    oqmultiple=pkgqty)
                    self.add_price(p)
        self.pkgqty = mpkgqty
        self.part_data = part_data

    def load_from_response(self, response):
        self._load_from_response(part_data=response)


class VendorArrow(VendorBase):
    _partclass = ArrowElnPart

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
        'CONN MODULAR', #'DIODE SMD', 'DIODE THRU', 'BRIDGE RECTIFIER',
        'VARISTOR', 'RES SMD', 'RES THRU',  # 'RES ARRAY SMD',
        'CAP CER SMD', 'CAP AL SMD', 'CAP MICA SMD',  # 'CAP TANT SMD',
        'TRANSFORMER SMD', 'INDUCTOR SMD', 'RELAY', 'CONN TERMINAL DMC',
        'CRYSTAL AT', 'CRYSTAL OSC', 'CRYSTAL VCXO', 'ZENER SMD'
    ]

    _type = 'Arrow REST API v3'

    _url_base = 'http://www.arrow.com/'
    _api_endpoint = 'http://api.arrow.com/itemservice/v3/en'

    _ident_blacklist = [
        'IC SMD AD7734BRUZ TSSOP28',
        'IC THRU DUAL PA96CE TO3-8-2',
        'IC SMD DAC5672AIPFB TQFP48-7',
    ]

    def __init__(self, apikey=ARROW_API_KEY, apilogin=ARROW_API_LOGIN,
                 sourcecd='NAC', **kwargs):
        if not apikey or not apilogin:
            raise Exception('Arrow needs an API KEY and LOGIN to be '
                            'specified in the tendril config')
        super(VendorArrow, self).__init__(**kwargs)
        self.add_order_additional_cost_component("Customs", 12.85)
        self._manufacturer_codes = None
        self._api_key = apikey
        self._api_login = apilogin
        self._sourcecd = sourcecd
        self._session = www.get_session()

    @property
    def _api_common_params(self):
        return {'login': self._api_login, 'apikey': self._api_key}

    @property
    def sourcecd(self):
        return self._sourcecd

    def apiresult_filter_sources(self, sources):
        for source in sources:
            if source['sourceCd'] != self.sourcecd:
                continue
            for sourcepart in source['sourceParts']:
                if sourcepart['inStock']:
                    yield source
                    break

    @staticmethod
    def apiresult_getminqty(sources):
        rv = None
        for source in sources:
            for sourcepart in source['sourceParts']:
                if 'Prices' not in sourcepart.keys():
                    continue
                mb = min([(br['minQty'], br['price'])
                          for br in sourcepart['Prices']['resaleList']],
                         key=lambda x: x[0])
                if rv is None or mb < rv:
                    rv = mb
        return rv

    def _api_search_token(self, token, rows=25, start=None, mfrcd=None):
        """
        Search for (paginated) items using a search token
        `search/token`
        """
        ep = self._api_endpoint + '/search/token?'
        params = self._api_common_params
        params['search_token'] = token
        params['rows'] = rows
        if mfrcd:
            params['mfrCd'] = mfrcd
        if start:
            params['start'] = start
        r = self._session.get(ep, params=params).json()['itemserviceresult']
        if not r['transactionArea'][0]['response']['success']:
            raise LookupError("Error searching for token")
        nresults = r['transactionArea'][0]['responseSequence']['totalItems']
        return nresults, r['data'][0]['PartList']

    def api_search_token(self, *args, **kwargs):
        nr, r = self._api_search_token(*args, start=0, **kwargs)
        nr -= len(r)
        while nr:
            _, lr = self._api_search_token(*args, start=len(r), **kwargs)
            nr -= len(lr)
            r.extend(lr)
        return r

    def api_search_list(self, parts):
        """
        Search for multiple items at once
        `search/list`
        """
        ep = self._api_endpoint + '/search/list?'
        raise NotImplementedError

    def api_lookup_manufacturer(self):
        """
        Map of manufacturers and corresponding codes
        `lookup/manufacturer`
        """
        ep = self._api_endpoint + '/lookup/manufacturer?'
        params = self._api_common_params
        r = self._session.get(ep, params=params).json()['itemserviceresult']
        if not r['transactionArea'][0]['response']['success']:
            raise LookupError("Error retrieving manufacturer lookup")
        mfrs = r['data'][0]['manufacturers']
        return {x['mfrCd']: x['mfrName'] for x in mfrs}

    @property
    def manufacturer_codes(self):
        if self._manufacturer_codes is None:
            self._manufacturer_codes = self.api_lookup_manufacturer()
        return self._manufacturer_codes

    def search_vpnos(self, ident):
        if ident in self._ident_blacklist:
            return None, 'BLACKLIST'
        parts, strategy = self._search_vpnos(ident)
        if parts is None:
            return None, strategy
        pnos = [x.pno for x in parts]

        try:
            # TODO Figure out how the mouser impl works without this mess :|
            with get_session() as s:
                dbvobj = controller.get_vendor(name=self.cname)
                controller.set_strategy(vendor=dbvobj, ident=ident,
                                        strategy=strategy, session=s)
                controller.set_amap_vpnos(vendor=dbvobj, ident=ident,
                                          vpnos=pnos, session=s)
                for part in parts:
                    partobj = self._partclass(part.pno, ident=ident,
                                              vendor=self, max_age=None,
                                              shell_only=True)
                    partobj.load_from_response(part.raw)
                    partobj.commit(session=s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            raise

        return pnos, strategy

    def _search_vpnos(self, ident):
        device, value, footprint = parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if check_for_std_val(ident):
                try:
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint)
            else:
                return None, 'FILTER_NODEVICE'
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    def _process_response_part(self, rpart):
        sources = [x for x in
                   self.apiresult_filter_sources(rpart['InvOrg']['sources'])]
        if not len(sources):
            ns = True
            minqty = None
            unitp = None
        else:
            ns = False
            minqty, unitp = self.apiresult_getminqty(sources)
        return SearchPart(pno=str(rpart['itemId']), mfgpno=rpart['partNum'],
                          package=rpart['packageType'], ns=ns,
                          unitp=unitp, minqty=minqty, raw=rpart)

    @staticmethod
    def _get_device_catstrings(device):
        return False, None

    def _filter_results_by_category(self, parts, device):
        raise NotImplementedError

    def _get_search_vpnos(self, device, value, footprint):
        try:
            r = self.api_search_token(token=value)
            nresults = len(r)
        except LookupError:
            return None, 'NORESULTS'
        if not nresults:
            return None, 'NORESULTS'
        parts = [self._process_response_part(x) for x in r]
        # Arrow seems occasionally return parts which have the same item id.
        # Such parts are currently ignored.
        # TODO figure out how to handle (merge?) these.
        parts = self._remove_duplicates(parts)
        footprint = None
        success, pnos, strategy = self._process_results(parts, value, footprint)
        pnos = set(pnos)
        parts = [x for x in parts if x.pno in pnos]
        return parts, strategy

    def _get_pas_vpnos(self, device, value, footprint):
        raise NotImplementedError


dvobj = VendorArrow(name='arrow', dname='Arrow Electronics, Inc',
                    pclass='electronics', mappath=None,
                    currency_code='USD', currency_symbol='US$',
                    apikey=ARROW_API_KEY, apilogin=ARROW_API_LOGIN)
