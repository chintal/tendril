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
ePass Vendor Module (:mod:`tendril.sourcing.ePass`)
===================================================

Vendor support module vendors accessible using element14's
`ePass API<http://in.element14.com/epass-api>`_. At first glance,
this seems to include a number of `Premier Farnell brands
<http://www.premierfarnell.com/our-company/our-brands>`_.

.. info::
    Deferred due to lack of API key validation.

.. info::
    To be developed and tested against element14 (Asia Pacific, IN) only.

"""

from tendril.utils import www
from tendril.utils import log

from .vendors import VendorBase
from .vendors import VendorElnPartBase

logger = log.get_logger(__name__, log.DEFAULT)


class EPassElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        super(EPassElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
        s = self._vendor.session
        params = self._vendor.api_base_params
        params.append(('term', 'id:{0}'.format(self.vpno)))
        params.append(('resultsSettings.responseGroup', 'large'))
        r = s.get(self._vendor.api_endpoint, params=params)
        pass


class VendorEPass(VendorBase):
    _partclass = EPassElnPart

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

    _type = 'ePass REST API'

    # TODO This is vendor specific, and should probably come from the config
    _url_base = 'http://in.element14.com'
    _search_url_base = 'https://api.element14.com/catalog/products'

    def __init__(self, apikey=None, **kwargs):
        self._api_key = apikey
        self._session = www.get_session(target=self._search_url_base)
        super(VendorEPass, self).__init__(**kwargs)

    @property
    def api_endpoint(self):
        return self._search_url_base

    @property
    def api_key(self):
        return self._api_key

    @property
    def api_base_params(self):
        return [
            ('callInfo.responseDataFormat', 'JSON'),
            ('storeInfo.id', 'in.element14.co'),
            ('callInfo.apiKey', self._api_key),
        ]

    @property
    def session(self):
        return self._session

    def search_vpnos(self, ident):
        return None, 'NOAPIKEY'


def __get_api_key():
    from tendril.utils.config import VENDORS_DATA
    vopts = None
    for v in VENDORS_DATA:
        if v['name'] == 'e14':
            vopts = v
            break
    if vopts is not None:
        return vopts['apikey']
    return None


dvobj = VendorEPass(name='e14', dname='element14 India Private Limited.',
                    pclass='electronics', mappath=None,
                    currency_code='USD', currency_symbol='US$',
                    apikey=__get_api_key())
