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
Mouser Sourcing Module documentation (:mod:`sourcing.mouser`)
=============================================================
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


class VendorMouser(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None):
        self.url_base = 'http://www.mouser.in/'
        self._devices = ['IC SMD',
                         'IC THRU',
                         'IC PLCC',
                         'FERRITE BEAD SMD',
                         'TRANSISTOR THRU',
                         'TRANSISTOR SMD',
                         'CONN DF13',
                         'CONN DF13 HOUS',
                         # 'CONN DF13 WIRE',
                         'CONN DF13 CRIMP',
                         'DIODE SMD',
                         'DIODE THRU',
                         'VARISTOR',
                         'BRIDGE RECTIFIER',
                         'RES SMD',
                         'RES THRU',
                         'CAP CER SMD',
                         'CAP TANT SMD',
                         'TRANSFORMER SMD',
                         'INDUCTOR SMD',
                         'CRYSTAL AT'
                         ]
        self._ndevices = []
        self._searchpages_filters = {}
        if not currency_code:
            currency_code = 'USD'
        if not currency_symbol:
            currency_symbol = 'US$'
        super(VendorMouser, self).__init__(name, dname, pclass, mappath,
                                           currency_code, currency_symbol)
        self._vpart_class = MouserElnPart
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
                    return self._get_search_vpnos(device, value,
                                                  footprint, ident)
                try:
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    # TODO This warning is necessary.
                    # Restore it when implemented.
                    # logger.warning(ident + ' :: Mouser Search for ' +
                    #                device +' Not Implemented')
                    return None, 'NOT_IMPL'
            if device in self._devices:
                return self._get_search_vpnos(device, value, footprint, ident)
            else:
                return None, 'FILTER_NODEVICE'
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('Fatal Error searching for : ' + ident)
            return None, None

    @staticmethod
    def _search_preprocess(device, value, footprint):
        # Hail Mary
        if footprint == 'TO-220':
            footprint = 'TO220'
        if footprint == 'TO-92':
            footprint = 'TO92'
        return device, value, footprint

    @staticmethod
    def _process_product_page(soup):
        # beablock = soup.find('td', 'beablock-notice')
        # if beablock is not None:
        #     if beablock.text == u'\nObsolete item\n':
        #         return False, None, 'OBSOLETE_NOTAVAIL'
        pdtable = soup.find('div', id='product-desc')
        if pdtable is not None:
            pno_cell = pdtable.find('div', id='divMouserPartNum')
            pno = pno_cell.text.encode('ascii', 'replace').strip()
            mfgpno = soup.find(
                'div', id='divManufacturerPartNum'
            ).text.strip()
            try:
                package = soup.find(
                    'span', text=re.compile('Package / Case')
                ).parent.find_next_sibling().text.strip().encode(
                    'ascii', 'replace'
                )
            except AttributeError:
                package = None
            # TODO Implement these
            ns = False
            part = (pno, mfgpno, package, ns)
            return True, [part], 'EXACT_MATCH'
        else:
            return False, None, ''

    @staticmethod
    def _get_resultpage_row_pno(row):
        pno = row.attrs['data-partnumber'].encode('ascii', 'replace')
        return pno

    @staticmethod
    def _get_resultpage_row_unitp(row):
        unitp_cell = row.find('span', id=re.compile(r'lblPrice'))
        unitp_string = unitp_cell.text.strip().encode('ascii', 'replace')
        unitp = None
        try:
            unitp = locale.atof(unitp_string.replace('$', ''))
        except ValueError:
            pass
        return unitp

    norms = [
        # --- Standard Cases --- #
        # SO8
        # SO-8
        # SOIC-Narrow-8
        # SOIC8 (Normalized)
        # SOIC-8
        (re.compile(ur'^(SO(IC)?(-Narrow)?-?(?P<pinc>[\d]+))$'), 'SOIC{0}', ['pinc']),  # noqa
        # TO220 (Normalized)
        # TO-220
        # TO-220-3
        (re.compile(ur'^TO-?220(-3)?$'), 'TO220', []),
        # TO-220-FP-3
        # TO-220-3 FP
        (re.compile(ur'^TO-?220(-3)?[- ](FP)(-3)?$'), 'TO220 FP', []),
        # PDIP-6
        # DIP6 (Normalized)
        (re.compile(ur'^P?DIP-?(?P<pinc>\d+)$'), 'DIP{0}', ['pinc']),

        # --- Somewhat Special Cases --- #
        # PDIP-6 Gull Wing
        # SMT6 (Normalized)
        (re.compile(ur'^P?DIP-?(?P<pinc>\d+)( Gull Wing)$'), 'SMT{0}', ['pinc']),  # noqa

        # --- Very Special Cases --- #
        # SOIC4
        # TO-269AA (Normalized)
        (re.compile(ur'^(SOIC-?4)|(TO-?269-?AA)$'), 'TO-269AA', []),
    ]

    def _standardize_package(self, package):
        # Mouser does not standardize packages,
        # and results in plenty of false negatives.
        for norm in self.norms:
            m = norm[0].match(package)
            if m:
                params = [m.group(var) for var in norm[2]]
                package = norm[1].format(*params)
        return package

    def _get_resultpage_row_package(self, row, header):
        try:
            header.index('Package / Case')
        except ValueError:
            return None
        package_col = header.index('Package / Case') + 1
        package = row.contents[package_col].text.strip()
        return self._standardize_package(package)

    @staticmethod
    def _get_resultpage_row_minqty(row):
        mq_cell = row.find('a', id=re.compile(r'lnkQuantity'))
        mq_string = mq_cell.text.strip().encode('ascii', 'replace')
        mq = None
        try:
            mq = locale.atof(mq_string.replace(':', ''))
        except ValueError:
            pass
        if mq_string == 'Not Available':
            return -1
        return mq

    @staticmethod
    def _get_resultpage_row_mfgpno(row):
        return row.find('a', id=re.compile(r'MfrPartNumberLink')).text

    def _process_resultpage_row(self, row, header):
        pno = self._get_resultpage_row_pno(row)
        unitp = self._get_resultpage_row_unitp(row)
        package = self._get_resultpage_row_package(row, header)
        if not package:
            try:
                vpart = MouserElnPart(pno)
                package = self._standardize_package(vpart.package)
            except AttributeError:
                pass
        minqty = self._get_resultpage_row_minqty(row)
        mfgpno = self._get_resultpage_row_mfgpno(row)
        if minqty == -1 or unitp is None:
            ns = True
        else:
            ns = False
        return pno, mfgpno, package, ns

    def _get_resultpage_parts(self, soup):
        ptable = soup.find(
            'table',
            id=re.compile(r'ctl00_ContentMain_SearchResultsGrid_grid')
        )
        if ptable is None:
            return False, None, 'NO_RESULTS:3'
        header_row = ptable.find(
            'tr', class_=re.compile(r'SearchResultColumnHeading')
        ).find_all('th')
        header = [x.text.strip() for x in header_row]
        rows = ptable.find_all('tr', class_=re.compile(r'SearchResultsRow'))
        if not rows:
            return False, None, 'NO_RESULTS:1'
        parts = []
        for row in rows:
            part = self._process_resultpage_row(row, header)
            if part[-1] is not None:
                parts.append(part)
        # check_package = ''
        # for part in parts:
        #     if part[2] is None:
        #         check_package = 'Wpack'
        return True, parts, ''

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
            if footprint in package:
                if not ns:
                    pnos.append(pno)
        if len(pnos) == 0:
            strategy += ' ALLOW NS'
            for pno, mfgpno, package, ns in parts:
                if footprint in package:
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
            # Did not find an exact match package.
            # Check for consensus package instead.
            result, cpackage, strategy = self._find_consensus_package(parts)
            if result is False:
                # No exact match, no consensus on package
                result, pnos, strategy = self._filter_results_byfootprint(
                    parts, footprint
                )
                return True, pnos, strategy

        # cpackage exists
        result, pnos, strategy = self._filter_results_bycpackage(
            parts, cpackage, strategy
        )

        if len(pnos) == 0:
            pnos = None

        return True, pnos, strategy

    @staticmethod
    def _prefilter_parts(parts, value):
        parts = [part for part in parts if value.upper() in part[1].upper()]
        return parts

    def _process_results_page(self, soup):
        result, parts, strategy = self._get_resultpage_parts(soup)
        if result is False:
            return False, None, strategy
        if parts is None:
            raise Exception
        if len(parts) == 0:
            return False, None, 'NO_RESULTS:2'
        # result, pnos, strategy = self._filter_results(
        #     parts, value, footprint
        # )
        return result, parts, strategy

    @staticmethod
    def _get_device_catstrings(device):
        if device.startswith('IC'):
            titles = ['Semiconductors', 'Sensors']
            catstrings = ['Integrated Circuits - ICs',
                          'Temperature Sensors']
            subcatstrings = 'all'
        elif device.startswith('DIODE'):
            titles = ['Semiconductors']
            catstrings = ['Discrete Semiconductors',
                          'Diodes & Rectifiers',
                          'Rectifiers',
                          'Schottky Diodes & Rectifiers',
                          'TVS Diodes']
            subcatstrings = 'all'
        elif device.startswith('BRIDGE RECTIFIER'):
            titles = ['Semiconductors']
            catstrings = ['Discrete Semiconductors',
                          'Bridge Rectifiers']
            subcatstrings = 'all'
        elif device.startswith('RES THRU'):
            titles = ['Passive Components']
            catstrings = ['Through Hole Resistors']
            subcatstrings = 'all'
        else:
            return False, None, None
        return True, catstrings, subcatstrings, titles

    def _get_cat_soup(self, soup, device, url, ident, i=0):
        # TODO rewrite this fuction from scratch
        ctable = soup.find('div', id='CategoryControlTop')
        sctable = soup.find('table', id='tblSplitCategories')
        if not ctable and not sctable:
            yield soup
        elif sctable:
            cat_dict = {}
            cat_title_divs = sctable.find_all(
                'div', class_='catTitleNoBorder'
            )
            for title_div in cat_title_divs:
                newurl = None
                cat_title = title_div.text.strip()
                subcatlist = title_div.find_next_siblings(
                    'ul', class_='sub-cats', limit=1
                )[0]
                subcats = subcatlist.find_all(
                    'a', attrs={'itemprop': 'significantLink'}
                )
                subcat_links = {x.text: x.attrs['href'] for x in subcats}
                cat_dict[cat_title] = subcat_links
                res, catstrings, subcatstrings, titles = self._get_device_catstrings(device)  # noqa
                cat_links = None
                for title in titles:
                    if title in cat_dict.keys():
                        cat_links = cat_dict[title]
                        break
                if not cat_links:
                    continue
                for catstring in catstrings:
                    if catstring in cat_links.keys():
                        newurl = urlparse.urljoin(url, cat_links[catstring])
                        break
                if not newurl:
                    continue
                soup = www.get_soup(newurl)
                ctable = soup.find('div', id='CategoryControlTop')
                if ctable:
                    soups = self._get_cat_soup(
                        soup, device, newurl, ident, i=i+1
                    )
                    for soup in soups:
                        yield soup
                else:
                    yield soup
        elif ctable:
            cats = ctable.find_all('a', attrs={'itemprop': 'significantLink'})
            cat_links = {x.text: x.attrs['href'] for x in cats}
            res, catstrings, subcatstrings, titles = self._get_device_catstrings(device)  # noqa
            newurl = None
            if i == 0:
                for catstring in catstrings:
                    if catstring in cat_links.keys():
                        newurl = urlparse.urljoin(url, cat_links[catstring])
                        break
                if newurl:
                    soup = www.get_soup(newurl)
                    ctable = soup.find('div', id='CategoryControlTop')
                    if ctable:
                        soups = self._get_cat_soup(
                            soup, device, newurl, ident, i=i+1
                        )
                        for soup in soups:
                            yield soup
                    else:
                        yield soup
            elif i == 1:
                if subcatstrings == 'all':
                    for cat_link in cat_links:
                        newurl = urlparse.urljoin(url, cat_links[cat_link])
                        soup = www.get_soup(newurl)
                        ctable = soup.find('div', id='CategoryControlTop')
                        if ctable:
                            soups = self._get_cat_soup(
                                soup, device, newurl, ident, i=i+1
                            )
                            for soup in soups:
                                yield soup
                        else:
                            yield soup
            elif i > 1:
                if subcatstrings == 'all':
                    for cat_link in cat_links:
                        newurl = urlparse.urljoin(url, cat_links[cat_link])
                        soup = www.get_soup(newurl)
                        yield soup
        else:
            raise Exception

    def _process_cat_soup(self, soup):
        ptable = soup.find(
            'table',
            id=re.compile(r'ctl00_ContentMain_SearchResultsGrid_grid')
        )
        if ptable is None:
            # check for single product page
            result, pnos, strategy = self._process_product_page(soup)
            if result is True:
                return True, pnos, strategy

            # check for no results
            nr_span = soup.find('span', class_='NRSearchMsg')
            if nr_span:
                nr_text = nr_span.text.strip()
                if nr_text == 'did not return any results.':
                    return True, None, 'NO_RESULTS_PAGE'

            raise NotImplementedError(
                "Expecting a results page or products page, "
                "not whatever this is"
            )
        return self._process_results_page(soup)

    def _get_search_vpnos(self, device, value, footprint, ident):
        if value.strip() == '':
            return None, 'NOVALUE'
        device, value, footprint = self._search_preprocess(
            device, value, footprint
        )
        url = urlparse.urljoin(
            self.url_base,
            "Search/Refine.aspx?Keyword={0}&Stocked=True".format(
                urllib.quote_plus(value)
            )
        )
        soup = www.get_soup(url)
        if soup is None:
            return None, 'URL_FAIL'

        parts = []
        strategy = ''
        for soup in self._get_cat_soup(soup, device, url, ident):
            result, lparts, lstrategy = self._process_cat_soup(soup)
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
        result, pnos, lstrategy = self._filter_results(parts, value, footprint)  # noqa
        if pnos:
            pnos = list(set(pnos))
            pnos = map(lambda x: html_parser.unescape(x), pnos)
        return pnos, ':'.join([strategy, lstrategy])

    @staticmethod
    def _get_searchurl_crystal():
        return 'http://www.mouser.in/Passive-Components/Frequency-Control-Timing-Devices/Crystals/_/N-6zu9f/'  # noqa

    def _get_pas_vpnos(self, device, value, footprint):
        raise NotImplementedError


class MouserElnPart(vendors.VendorElnPartBase):
    def __init__(self, mouserpartno, ident=None, vendor=None):
        if vendor is None:
            vendor = VendorMouser('mouser', 'transient', 'electronics',
                                  currency_code='USD', currency_symbol='US$')
        super(MouserElnPart, self).__init__(mouserpartno, ident, vendor)
        self.url_base = vendor.url_base
        if not self._vpno:
            logger.error("Not enough information to create a Mouser Part")
        self._get_data()

    def _get_data(self):
        soup = self._get_product_soup()
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
            logger.error("Failed to acquire part information : " + self.vpno)
            # TODO raise AttributeError

    def _get_product_soup(self):
        start_url = urlparse.urljoin(
            self.url_base,
            '/Search/Refine.aspx?Keyword={0}&FS=True'.format(
                urllib.quote_plus(self.vpno)
            )
        )
        soup = www.get_soup(start_url)
        url = www.get_actual_url(start_url)
        # TODO start_url may not be the actual URL.
        # Handle this or remove the redirect handler.
        if soup is None:
            logger.error(
                "Unable to open Mouser product start page : " + self.vpno
            )
            return
        if soup.find('div', id='productdetail-box1'):
            return soup
        else:
            stable = soup.find(
                'table',
                id=re.compile(r'ctl00_ContentMain_SearchResultsGrid_grid')
            )
            srow = stable.find('tr', {'data-partnumber': self.vpno},
                               class_=re.compile(r'SearchResultsRow'))
            link = srow.find('a', id=re.compile(r'lnkMouserPartNumber'))
            href = urlparse.urljoin(url, link.attrs['href'])
            soup = www.get_soup(href)
            return soup

    def _get_prices(self, soup):
        ptable = soup.find(id='ctl00_ContentMain_divPricing')
        prices = []
        rows = [x.find_parent('div').find_parent('div')
                for x in ptable.find_all('span', id=re.compile(r'ctl00_ContentMain_ucP_rptrPriceBreaks_ctl(\d+)_lblPrice'))  # noqa
                ]
        for row in rows:
            moq_text = row.find(id=re.compile('lnkQuantity')).text
            rex_qtyrange = re.compile(ur'SelectMiniReelQuantity\(((?P<minq>\d+),(?P<maxq>\d+))\)')  # noqa
            rex_qty = re.compile(ur'SelectQuantity\((?P<minq>\d+)\)')
            try:
                m = rex_qty.search(row.find('a', id=re.compile('lnkQuantity')).attrs['href'])  # noqa
            except KeyError:
                # TODO make sure this holds
                continue
            maxq = None
            if m is None:
                m = rex_qtyrange.search(row.find('a', id=re.compile('lnkQuantity')).attrs['href'])  # noqa
                if m is None:
                    raise ValueError(
                        "Error parsing qty range while acquiring moq for " +
                        self.vpno
                    )
                maxq = locale.atoi(m.group('maxq'))
            minq = locale.atoi(m.group('minq'))
            price_text = row.find(id=re.compile('lblPrice')).text
            try:
                moq = locale.atoi(moq_text)
                if moq != minq:
                    raise ValueError(
                        "minq {0} does not match moq {1} for {2}".format(
                            str(minq), str(moq), self.vpno
                        )
                    )
                if not maxq or minq != maxq:
                    oqmultiple = 1
                else:
                    oqmultiple = minq
            except ValueError:
                raise ValueError(
                    moq_text + " found while acquiring moq for " + self.vpno
                )
            try:
                price = locale.atof(price_text.replace('$', ''))
            except ValueError:
                if price_text.strip() == 'Quote':
                    # TODO handle this somehow?
                    continue
                else:
                    raise ValueError(
                        price_text + " found while acquiring price for " +
                        self.vpno
                    )
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
        if not n:
            return ''
        try:
            package_cell = n.parent.find_next_sibling()
            package = package_cell.text.strip().encode('ascii', 'replace')
        except IndexError:
            package = ''
        return package

    @staticmethod
    def _get_datasheet_link(soup):
        datasheet_div = soup.find('div', id=re.compile('divCatalogDataSheet'))
        if not datasheet_div:
            return
        datasheet_link = datasheet_div.find_all(
            'a', text=re.compile('Data Sheet')
        )[0].attrs['href']
        return datasheet_link.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_avail_qty(soup):
        n = soup.find('div', id='availability')
        n = n.findChild(text=re.compile('Stock')).parent.parent.find_next_sibling()  # noqa
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
