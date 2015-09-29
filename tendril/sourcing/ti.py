#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
TI Sourcing Module documentation (:mod:`sourcing.ti`)
=====================================================
"""

import locale
import re
import urllib
import urlparse
import HTMLParser
import traceback

import vendors
from tendril.utils import www
from tendril.conventions import electronics

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
html_parser = HTMLParser.HTMLParser()


class VendorTI(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None):
        self.url_base = 'https://store.ti.com'
        self._devices = ['IC SMD',
                         'IC THRU',
                         'IC PLCC',
                         ]
        self._ndevices = []
        self._searchpages_filters = {}
        if not currency_code:
            currency_code = 'USD'
        if not currency_symbol:
            currency_symbol = 'US$'
        super(VendorTI, self).__init__(name, dname, pclass, mappath,
                                       currency_code, currency_symbol)
        self._vpart_class = TIElnPart
        self.add_order_baseprice_component("Shipping Cost", 7)
        self.add_order_additional_cost_component("Customs", 12.85)

    def get_vpart(self, vpartno, ident=None):
        if issubclass(TIElnPart, vendors.VendorElnPartBase):
            return TIElnPart(vpartno, ident, self)
        else:
            raise TypeError

    def search_vpnos(self, ident):
        device, value, footprint = electronics.parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            return self._get_search_vpnos(device, value, footprint)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    @staticmethod
    def _search_preprocess(device, value, footprint):
        if footprint in ['TO220', 'TO-220']:
            footprint = 'TO-220-3'
        elif footprint in ['TO92', 'TO-92']:
            footprint = 'TO-92-3'
        return device, value, footprint

    norms = [
        # --- Standard Cases --- #
        # TO-220-3 (Normalized)
        # http://www.ti.com/sc/docs/psheets/type/to_220.html
        # KC-3
        # KC-5
        # KC-7
        # KCS-3
        # KCT-3
        # KV-11
        # KV-5
        # KV-7
        # KVT-7
        # NDA-11
        # NDB-15
        # NDD-3
        # NDE-3
        # NDF-3
        # NDG-3
        # NDH-5
        # NDK-11
        # NDL-15
        # NDZ-7
        # NEB03A-3
        # NEB03F-3
        # NEB03G-3
        # NEB05B-5
        # NEB05E-5
        # NEB05F-5
        # NEK-15
        (re.compile(ur'^((K((C[ST]?)|(VT?)))|(ND[ABDEFGHKLZ])|(NEB0((3[AFG])|(5[BEF])))|(NEK))-(?P<pinc>\d+)$'),  # noqa
         'TO-220-{0}', ['pinc']),
    ]

    def _standardize_package(self, package):
        for norm in self.norms:
            m = norm[0].match(package)
            if m:
                params = [m.group(var) for var in norm[2]]
                package = norm[1].format(*params)
        return package

    def _process_resultpage_row(self, row):
        product_link = row.find('a', class_='highlight')
        pno = product_link.text.strip()
        try:
            product = TIElnPart(pno)
        except:
            return None, None, None, None
        # unitp = product._prices[0]._price
        ns = False
        mfgpno = pno
        package = self._standardize_package(product.package)
        return pno, mfgpno, package, ns

    def _process_search_soup(self, soup):
        ptable = soup.find('table',
                           id=re.compile(r'ctl00_ProductList'))
        if ptable is None:
            return False, None, 'NO_RESULTS:3'
        rows = ptable.find_all('td', class_=re.compile(r'tableNode'))
        if not rows:
            return False, None, 'NO_RESULTS:1'
        parts = []
        for row in rows:
            part = self._process_resultpage_row(row)
            if part[-1] is not None:
                parts.append(part)
        return True, parts, ''

    @staticmethod
    def _prefilter_parts(parts, value):
        parts = [part for part in parts if value.upper() in part[1].upper()]
        return parts

    @staticmethod
    def _find_exact_match_package(parts, value):
        for pno, mfgpno, package, ns in parts:
            if mfgpno == value:
                return True, package, 'EXACT_MATCH_FFP'
        return False, None, None

    @staticmethod
    def _find_consensus_package(parts):
        cpackage = parts[0][2]
        for pno, mfgpno, package, ns in parts:
            if package != cpackage:
                cpackage = None
        if cpackage is not None:
            return True, cpackage, 'CONSENSUS_FP_MATCH'
        return False, None, None

    @staticmethod
    def _filter_results_unfiltered(parts):
        pnos = []
        strategy = 'UNFILTERED'
        for pno, mfgpno, package, ns in parts:
            if not ns:
                pnos.append(pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for pno, mfgpno, package, ns in parts:
                pnos.append(pno)
        return True, pnos, strategy

    @staticmethod
    def _filter_results_byfootprint(parts, footprint):
        pnos = []
        strategy = 'HAIL MARY'
        for pno, mfgpno, package, ns in parts:
            if footprint == package:
                if not ns:
                    pnos.append(pno)
        if len(pnos) == 0:
            strategy += ' ALLOW NS'
            for pno, mfgpno, package, ns in parts:
                if footprint == package:
                    pnos.append(pno)
        return True, pnos, strategy

    @staticmethod
    def _filter_results_bycpackage(parts, cpackage, strategy):
        pnos = []
        for pno, mfgpno, package, ns in parts:
            if package == cpackage:
                if not ns:
                    pnos.append(pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for pno, mfgpno, package, ns in parts:
                if package == cpackage:
                    pnos.append(pno)
        return True, pnos, strategy

    def _filter_results(self, parts, value, footprint):
        if parts[0][2] is None or footprint is None:
            # No package, so no basis to filter
            result, pnos, strategy = self._filter_results_unfiltered(parts)
            return True, pnos, strategy

        # Find Exact Match Package
        result, cpackage, strategy = self._find_exact_match_package(parts,
                                                                    value)
        if result is False:
            # Did not find an exact match package. Check for consensus
            # package instead.
            result, cpackage, strategy = self._find_consensus_package(parts)
            if result is False:
                # No exact match, no consensus on package
                result, pnos, strategy = \
                    self._filter_results_byfootprint(parts, footprint)
                return True, pnos, strategy

        # cpackage exists
        result, pnos, strategy = \
            self._filter_results_bycpackage(parts, cpackage, strategy)

        if len(pnos) == 0:
            pnos = None

        return True, pnos, strategy

    @staticmethod
    def _get_search_soups(soup):
        yield soup

    def _get_search_vpnos(self, device, value, footprint):
        if value.strip() == '':
            return None, 'NOVALUE'
        device, value, footprint = \
            self._search_preprocess(device, value, footprint)
        url = urlparse.urljoin(self.url_base,
                               "Search.aspx?k={0}&pt=-1".format(
                                   urllib.quote_plus(value)))
        soup = www.get_soup(url)
        if soup is None:
            return None, 'URL_FAIL'
        parts = []
        strategy = ''
        for soup in self._get_search_soups(soup):
            result, lparts, lstrategy = self._process_search_soup(soup)
            if result:
                if lparts:
                    parts.extend(lparts)
                strategy += ', ' + lstrategy
            strategy = '.' + strategy
        if not len(parts):
            return None, strategy + ':NO_RESULTS:COLLECTED'
        parts = self._prefilter_parts(parts, value)
        if not len(parts):
            return None, strategy + ':NO_RESULTS:PREFILTER'
        result, pnos, lstrategy = \
            self._filter_results(parts, value, footprint)
        if pnos:
            pnos = list(set(pnos))
            pnos = map(lambda x: html_parser.unescape(x), pnos)
        return pnos, ':'.join([strategy, lstrategy])


class TIElnPart(vendors.VendorElnPartBase):
    def __init__(self, tipartno, ident=None, vendor=None):
        if vendor is None:
            vendor = VendorTI('ti', 'transient', 'electronics',
                              currency_code='USD', currency_symbol='US$')
        super(TIElnPart, self).__init__(tipartno, ident, vendor)
        self.url_base = vendor.url_base
        if not self._vpno:
            logger.error("Not enough information to create a TI Part")
        self._get_data()

    def _get_data(self):
        soup = self._get_product_soup()
        for price in self._get_prices(soup):
            self.add_price(price)
        try:
            self.mpartno = self._get_mpartno()
            self.manufacturer = self._get_manufacturer()
            self.datasheet = self._get_datasheet_link()
            self.vpartdesc = self._get_description(soup)
            self.package = self._get_package(soup)
        except AttributeError:
            logger.error("Failed to acquire part information : " + self.vpno)
            # TODO raise AttributeError

    def _get_product_soup(self):
        start_url = urlparse.urljoin(
            self.url_base,
            "Search.aspx?k={0}&pt=-1".format(urllib.quote_plus(self.vpno))
        )
        soup = www.get_soup(start_url)
        ptable = soup.find('table',
                           id=re.compile(r'ctl00_ProductList'))
        if ptable is None:
            raise ValueError("No result list founds for " + self.vpno)
        rows = ptable.find_all('td', class_=re.compile(r'tableNode'))
        if not rows:
            raise ValueError("No results founds for " + self.vpno)

        product_url = None
        for row in rows:
            product_link = row.find('a', class_='highlight')
            pno = product_link.text.strip()
            if pno.strip() == self.vpno.strip():
                product_url = urlparse.urljoin(self.url_base,
                                               product_link.attrs['href'])
                break

        if not product_url:
            raise ValueError("Exact match not found for " + self.vpno)

        soup = www.get_soup(product_url)
        if soup is None:
            logger.error("Unable to open TI product page : " + self.vpno)
            return
        return soup

    rex_price = re.compile(ur'^((?P<start>\d+)-)?(?P<end>\d+)$')

    def _get_prices(self, soup):
        ptable = soup.find('div',
                           id='ctl00_ctl00_NestedMaster_PageContent'
                              '_ctl00_BuyProductDialog1_tierPricing')
        prices = []
        rows = ptable.find_all('div', class_=re.compile(r'pMoreLine'))
        availq = None
        for row in rows:
            price_text = row.find(
                'span', id=re.compile(r'lblTier(\d+)ListPrice')
            ).text.strip()
            price = locale.atof(price_text.replace('$', ''))
            qty_text = row.find('span', class_='qty').text.strip()
            m = self.rex_price.match(qty_text)
            if not m:
                raise ValueError(
                    "Didn't get a qty from " + qty_text + " for " + self.vpno
                )
            try:
                moq = locale.atoi(m.group('start'))
            except AttributeError:
                moq = locale.atoi(m.group('end'))
            maxq = locale.atoi(m.group('end'))
            if not availq or maxq > availq:
                availq = maxq
            price_obj = vendors.VendorPrice(moq,
                                            price,
                                            self._vendor.currency,
                                            oqmultiple=1)
            prices.append(price_obj)
        self.vqtyavail = availq
        return prices

    def _get_mpartno(self):
        return self.vpno

    @staticmethod
    def _get_manufacturer():
        return 'Texas Instruments'

    @staticmethod
    def _get_package(soup):
        pack = soup.find('span', id=re.compile('ctl00_Package')).text.strip()
        pin = soup.find('span', id=re.compile('ctl00_PIN')).text.strip()
        package = '-'.join([pack, pin])
        return package

    @staticmethod
    def _get_datasheet_link():
        return None

    @staticmethod
    def _get_description(soup):
        desc_cell = soup.find('tr', id=re.compile('trSku'))
        strings = []
        for string in desc_cell.stripped_strings:
            strings.append(string)
        return www.strencode(strings[1])
