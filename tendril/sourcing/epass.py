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
    Developed and tested against element14 (Asia Pacific, IN) only.

"""

import urlparse

from tendril.utils import www
from tendril.utils import log

from .vendors import VendorBase
from .vendors import VendorElnPartBase

logger = log.get_logger(__name__, log.DEFAULT)


class EPassElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        super(EPassElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
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

    _type = 'ePass'

    # TODO This is vendor specific
    _url_base = 'https://api.element14.com'
    _vendorlogo = '/static/images/vendor-logo-e14.png'
    _search_url_base = urlparse.urljoin(_url_base, '/catalog/products')

    def __init__(self, apikey=None, **kwargs):
        self._apikey = apikey
        self._session = www.get_session(target=self._url_base)
        super(VendorEPass, self).__init__(**kwargs)

    @property
    def apikey(self):
        return self._apikey

    @property
    def session(self):
        return self._session

    def search_vpnos(self, ident):
        pass
