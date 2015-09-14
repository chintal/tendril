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
Mouser Sourcing Module documentation (:mod:`sourcing.digikey`)
==============================================================
"""

import locale
import re
import urllib
import urlparse
import traceback

from bs4 import BeautifulSoup

import vendors
from tendril.utils import www
from tendril.utils.types import currency
from tendril.conventions import electronics

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


class VendorMouser(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None, currency_code=None, currency_symbol=None, ):
        self.url_base = 'http://www.mouser.in/'
        self._devices = ['IC SMD']
        self._ndevices = []
        self._searchpages_filters = {}
        super(VendorMouser, self).__init__(name, dname, pclass, mappath, currency_code, currency_symbol)
        self.add_order_baseprice_component("Shipping Cost", 40)
        self.add_order_additional_cost_component("Customs", 12.85)

    def get_vpart(self, vpartno, ident=None):
        if issubclass(MouserElnPart, vendors.VendorElnPartBase):
            return MouserElnPart(vpartno, ident, self)
        else:
            raise TypeError

    def search_vpnos(self, ident):
        device, value, footprint = electronics.parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if device.startswith('RES') or device.startswith('POT') or \
                    device.startswith('CAP') or device.startswith('CRYSTAL'):
                if electronics.check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value, footprint)
                try:
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    logger.warning(ident + ' :: DK Search for ' + device + ' Not Implemented')
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint)
            else:
                return None, 'FILTER_NODEVICE'
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None


class MouserElnPart(vendors.VendorElnPartBase):
    def __init__(self, mouserpartno, ident=None, vendor=None):
        """

        :type vendor: VendorDigiKey
        """
        if vendor is None:
            vendor = VendorMouser('mouser', 'transient', 'electronics',
                                  currency_code='USD', currency_symbol='US$')
        super(MouserElnPart, self).__init__(ident, vendor)
        self.url_base = vendor.url_base
        if mouserpartno is not None:
            self.vpno = mouserpartno
        else:
            logger.error("Not enough information to create a Mouser Part")
        self._get_data()

    def _get_data(self):
        soup, url = self._get_product_soup()
        for price in self._get_prices(soup):
            self.add_price(price)
        try:
            self.mpartno = self._get_mpartno(soup)
            self.manufacturer = self._get_manufacturer(soup)
            self.datasheet = self._get_datasheet_link(soup)
            self.vpartdesc = self._get_description(soup)
            self.vqtyavail = self._get_avail_qty(soup)
            self.package = self._get_package(soup)
        except AttributeError:
            logger.error("Failed to acquire part information : " + self.vpno + url)
            # TODO raise AttributeError

    def _get_product_soup(self):
        start_url = urlparse.urljoin(self.url_base,
                                     '/_/?Keyword={0}&FS=True'.format(
                                        urllib.quote_plus(self.vpno)))
        page = www.urlopen(start_url)
        if page is None:
            logger.error("Unable to open Mouser product start page : " + self.vpno)
            return
        if 'ProductDetail' in page.geturl():
            logger.debug("Got product page : " + page.geturl())
            soup = BeautifulSoup(page)
            return soup, page.geturl()
        else:
            soup = BeautifulSoup(page)
            stable = soup.find('table',
                               id=re.compile(r'ctl00_ContentMain_SearchResultsGrid_grid'))
            srow = stable.find('tr', {'data-partnumber' : self.vpno},
                               class_=re.compile(r'SearchResultsRow'))
            link = srow.find('a', id=re.compile(r'lnkMouserPartNumber'))
            href = urlparse.urljoin(page.geturl(), link.attrs['href'])
            product_page = www.urlopen(href)
            soup = BeautifulSoup(product_page)
            return soup, product_page.geturl()

    def _get_prices(self, soup):
        ptable = soup.find(id='ctl00_ContentMain_divPricing')
        prices = []
        rows = [x.find_parent('div').find_parent('div')
                for x in ptable.find_all(
                'span', id=re.compile(r'ctl00_ContentMain_ucP_rptrPriceBreaks_ctl(\d+)_lblPrice'))]
        for row in rows:
            moq_text = row.find(id=re.compile('lnkQuantity')).text
            rex_qtyrange = re.compile(ur'SelectMiniReelQuantity\(((?P<minq>\d+),(?P<maxq>\d+))\)')
            rex_qty = re.compile(ur'SelectQuantity\((?P<minq>\d+)\)')
            m = rex_qty.search(row.find('a', id=re.compile('lnkQuantity')).attrs['href'])
            maxq = None
            if m is None:
                m = rex_qtyrange.search(row.find('a', id=re.compile('lnkQuantity')).attrs['href'])
                if m is None:
                    print row.find('a', id=re.compile('lnkQuantity')).attrs['href']
                    raise ValueError("Error parsing qty range while acquiring moq for " + self.vpno)
                maxq = locale.atoi(m.group('maxq'))
            minq = locale.atoi(m.group('minq'))
            price_text = row.find(id=re.compile('lblPrice')).text
            try:
                moq = locale.atoi(moq_text)
                if moq != minq:
                    raise ValueError("minq {0} does not match moq {1} for {2}".format(
                        str(minq), str(moq), self.vpno))
                if not maxq or minq != maxq:
                    oqmultiple = 1
                else:
                    oqmultiple = minq
            except ValueError:
                raise ValueError(moq_text + " found while acquiring moq for " + self.vpno)
            try:
                price = locale.atof(price_text.replace('$', ''))
            except ValueError:
                raise ValueError(price_text + " found while acquiring price for " + self.vpno)
            price_obj = vendors.VendorPrice(moq,
                                            price,
                                            self._vendor.currency,
                                            oqmultiple=oqmultiple)
            prices.append(price_obj)
        return prices

    @staticmethod
    def _get_mpartno(soup):
        mpart = soup.find('div', id='divManufacturerPartNum')
        return mpart.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_manufacturer(soup):
        mfrer_div = soup.find('h2', attrs={'itemprop': "manufacturer"})
        mfrer = mfrer_div.find('a')
        return mfrer.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_package(soup):
        n = soup.find('span', text=re.compile('Package / Case'))
        try:
            package_cell = n.parent.find_next_sibling()
            package = package_cell.text.strip().encode('ascii', 'replace')
        except IndexError:
            package = ''
        return package

    @staticmethod
    def _get_datasheet_link(soup):
        datasheet_div = soup.find('div', id=re.compile('divCatalogDataSheet'))
        datasheet_link = datasheet_div.find_all('a', text=re.compile('Data Sheet'))[0].attrs['href']
        return datasheet_link.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_avail_qty(soup):
        n = soup.find('div', id='availability')
        n = n.findChild(text=re.compile('Stock')).parent.parent.find_next_sibling()
        qtytext = n.text.strip().encode('ascii', 'replace')
        rex = re.compile(r'^(?P<qty>[\d,]+)')
        qtytext = rex.search(qtytext).groupdict()['qty'].replace(',', '')
        return int(qtytext)
        # except:
        #     rex2 = re.compile(r'^Value Added Item')
        #     if rex2.match(n.text.strip().encode('ascii', 'replace')):
        #         return -2
        #     return -1

    @staticmethod
    def _get_description(soup):
        try:
            desc_cell = soup.find('span', attrs={'itemprop': 'description'})
            return desc_cell.text.strip().encode('ascii', 'replace')
        except:
            return ''
