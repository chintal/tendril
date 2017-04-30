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
Evelta Vendor Module (:mod:`tendril.sourcing.evelta`)
=====================================================
"""


import re
import locale
import traceback

from six.moves.urllib.parse import urlencode
from six.moves.urllib.parse import urlparse

from bs4 import element

from .vendorbase import VendorBase
from .vendorbase import VendorElnPartBase
from .vendorbase import VendorPrice
from .vendorbase import SearchResult
from .vendorbase import SearchPart
from .vendorbase import VendorPartInaccessibleError

from tendril.utils.www import get_soup
from tendril.conventions.electronics import check_for_std_val
from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import parse_resistor
from tendril.conventions.electronics import parse_capacitor

from tendril.sourcing.db import controller
from tendril.utils.db import get_session
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


class EveltaElnPart(VendorElnPartBase):
    def __init__(self, vpno, **kwargs):
        if not vpno and not kwargs['shell_only']:
            logger.error("Not enough information to create a Evelta Part")
        if kwargs.get('vendor', None) is None:
            kwargs['vendor'] = dvobj
        super(EveltaElnPart, self).__init__(vpno, **kwargs)

    def _get_data(self):
        # Given a part number, we can't reliably get to the part page.
        raise VendorPartInaccessibleError

    def load_from_response(self, response):
        self._load_from_response(response)

    _desc_handlers = {
        'Brand:': (element.Tag, 'a', 'manufacturer',
                   lambda x: str(x.text).strip()),
        'Product Code:': (element.NavigableString, None, 'vpno',
                          lambda x: str(x).strip()),
        'Availability:': (element.Tag, 'span', 'vqtyavail',
                          lambda x: None if x.text == 'In Stock' else 0)
    }

    def _load_description_table(self, soup):
        dtable = soup.find('div', attrs={'class': 'description'})
        dhandler = None
        for child in dtable.childGenerator():
            if not dhandler:
                if isinstance(child, element.NavigableString):
                    continue
                if isinstance(child, element.Tag) and child.name == 'span':
                    if child.text in self._desc_handlers.keys():
                        dhandler = self._desc_handlers[child.text]
            else:
                if isinstance(child, dhandler[0]):
                    if dhandler[1]:
                        if child.name != dhandler[1]:
                            continue
                    value = dhandler[3](child)
                    setattr(self, dhandler[2], value)
                    dhandler = None

    _regex_min = re.compile(r"This product has a minimum quantity of (?P<min>\d+)")  # noqa
    _regex_dis = re.compile(r"(?P<oq>\d+) or more \S(?P<pr>[\d.]+)")  # noqa

    def _load_base_price(self, soup):
        p = soup.find('span', attrs={'itemprop': 'price'}).text
        price = locale.atof(re.findall('[\d.]+', p)[0])
        m = soup.find('div', attrs={'class': 'minimum'}).text
        moq = int(self._regex_min.match(m).group('min'))
        self.add_price(VendorPrice(moq, price, self._vendor.currency))

    def _load_discount_price(self, soup):
        d = soup.find('div', attrs={'class': 'discount'}).text.strip()
        m = self._regex_dis.match(d)
        price = locale.atof(m.group('pr'))
        moq = int(m.group('oq'))
        self.add_price(VendorPrice(moq, price, self._vendor.currency))

    def _load_datasheet(self, soup):
        desc = soup.find('div', attrs={'id': 'tab-description'})
        links = desc.findAll('a')
        for link in links:
            name = link.contents[0]
            target = link.attrs['href']
            if name == 'Datasheet':
                self.datasheet = target

    def _load_url(self, soup):
        bc = soup.find('ul', attrs={'class': 'breadcrumb'})
        elem = bc.findAll('li')[-1]
        link = elem.find('a')
        o = urlparse(link.attrs['href'])
        self.vparturl = o.scheme + "://" + o.netloc + o.path

    def _load_from_response(self, soup):
        self.raw = soup
        self.vpartdesc = soup.find('h1', attrs={'itemprop': 'name'}).text
        self._load_description_table(soup)
        self._load_base_price(soup)
        self._load_discount_price(soup)
        self._load_datasheet(soup)
        self._load_url(soup)

    @property
    def mpartno(self):
        return self.vpno


def _res_smd_searchterm(device, value, footprint):
    v = parse_resistor(value, context={'device': device,
                                       'footprint': footprint})
    parts = ['RES SMD', v.resistance, v.tolerance, footprint]
    parts = [str(x) for x in parts if x]
    return ' '.join(parts)


def _res_smd_sanitycheck(name, device, value, footprint):
    v = parse_resistor(value, context={'device': device,
                                       'footprint': footprint})
    if not name.startswith(str(v.resistance)):
        return False
    return True


def _cap_cer_smd_searchterm(device, value, footprint):
    v = parse_capacitor(value, context={'device': device,
                                        'footprint': footprint})
    parts = [v.capacitance.fmt_repr('%v %u'), v.voltage, footprint, 'SMD']
    parts = [str(x) for x in parts if x]
    return ' '.join(parts)


def _cap_cer_smd_sanitycheck(name, device, value, footprint):
    v = parse_capacitor(value, context={'device': device,
                                        'footprint': footprint})
    if not name.startswith(v.capacitance.fmt_repr('%v %u')):
        return False
    return True


class VendorEvelta(VendorBase):
    _partclass = EveltaElnPart
    _vendorlogo = '/static/images/vendor-logo-evelta.png'
    _url_base = 'http://www.evelta.com'
    _searchurl_base = 'http://www.evelta.com/index.php'
    _devices = ['RES SMD', 'CAP CER SMD']
    _type = 'Evelta'

    def __init__(self, name, dname, pclass, **kwargs):
        super(VendorEvelta, self).__init__(name, dname, pclass, **kwargs)
        # self.add_order_additional_cost_component("CST", 12.85)
        self.add_order_baseprice_component("Shipping Cost", 85)

    def search_vpnos(self, ident):
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
                                              vendor=self, shell_only=True)
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
            if device.startswith('RES') or device.startswith('POT') or \
                    device.startswith('CAP') or device.startswith('CRYSTAL'):
                if check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value,
                                                  footprint, ident)
                try:
                    return self._get_pas_vpnos(device, value, footprint, ident)
                except NotImplementedError:
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint, ident)
            else:
                return None, 'FILTER_NODEVICE'
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    @staticmethod
    def _get_search_vpnos(device, value, footprint, ident):
        return None, 'NOT_IMPL'

    # TODO Add category to default params?
    _pas_searchparams = {
        'RES SMD': (_res_smd_searchterm,
                    _res_smd_sanitycheck, None),
        'CAP CER SMD': (_cap_cer_smd_searchterm,
                        _cap_cer_smd_sanitycheck, None),
        'CAP CER THRU': (None, None, None),
    }

    def _get_device_searchparams(self, device):
        return self._pas_searchparams[device]

    def _get_pas_vpnos(self, device, value, footprint, ident):
        stconstr, _, params = self._get_device_searchparams(device)
        searchterm = stconstr(device, value, footprint)
        if not params:
            params = {}
        params.update({'search': searchterm})
        return self._get_search_results(params, ident)

    def _process_resultpage_row(self, row, ident):
        d, v, f = parse_ident(ident)
        sanitycheck = self._get_device_searchparams(d)[1]
        name_cell = row.find(attrs={'class': 'name'})
        link = name_cell.find('a')
        name = link.contents[0]
        if not sanitycheck(name, d, v, f):
            return None
        o = urlparse(link.attrs['href'])
        uri = o.scheme + "://" + o.netloc + o.path
        try:
            part = self._partclass(vpno=None, ident=ident, vendor=self,
                                   shell_only=True)
            response = get_soup(uri)
            part.load_from_response(response)
        except:
            raise
        if part.vqtyavail is None:
            ns = False
        else:
            ns = True
        unitp = part.prices[0].unit_price
        minqty = part.abs_moq
        raw = part.raw
        return SearchPart(part.vpno, part.mpartno, None, ns, unitp, minqty, raw)

    def _process_search_soup(self, soup, ident):
        table = soup.find(attrs={'class': 'products_holder'})
        if not table:
            return SearchResult(False, None, 'NORESULTS')
        rows = table.find_all(attrs={'class': 'information_wrapper'})
        parts = [self._process_resultpage_row(x, ident) for x in rows]
        parts = [x for x in parts if x]
        if len(parts):
            result = True
        else:
            result = False
        return SearchResult(result, parts, 'SCAFFOLDED')

    def _get_search_results(self, sparams, ident):
        params = {'limit': 100, 'route': 'product/search'}
        params.update(sparams)
        params = urlencode(params)
        url = '?'.join([self._searchurl_base, params])
        soup = get_soup(url)
        parts = []
        strategy = ''
        for soup in self._get_search_soups(soup):
            sr = self._process_search_soup(soup, ident)
            if sr.success is True:
                if sr.parts:
                    parts.extend(sr.parts)
                strategy += ', ' + sr.strategy
            strategy = '.' + strategy
        if not len(parts):
            return None, strategy + ':NO_RESULTS:COLLECTED'
        return parts, strategy

    @staticmethod
    def _get_search_soups(soup):
        yield soup


dvobj = VendorEvelta('evelta', 'Evelta Electronics Pvt. Ltd.', 'electronics')
