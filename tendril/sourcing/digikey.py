# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
Digi-Key Sourcing Module documentation (:mod:`sourcing.digikey`)
================================================================

'Standalone' Usage
------------------

This module can be imported by itself to provide limited but
potentially useful functionality.

>>> from tendril.sourcing import digikey

.. rubric:: Search

Search for Digi-Key part numbers given a Tendril-compatible
ident string :

>>> digikey.dvobj.search_vpnos('IC SMD W5300 LQFP100-14')
(['1278-1009-ND'], 'EXACT_MATCH_FFP')

Note that only certain types of components are supported by the
search. The DEVICE component of the ident string is used to
determine whether or not a search will even be attempted.

Even with supported device types, remember that this search is
nowhere near bulletproof. The more generic a device and/or it's
name becomes, the less likely it is to work. The intended use
for this type of search is in concert with an organization's
engineering policies and an instance administrator who can make
the necessary tweaks to the search algortihms and maintain a
low error rate for component types commonly used within the
instance.

Tweaks and improvements to the search process are welcome as
pull requests to the tendril github repository, though their
inclusion will be predicated on them causing minimal breakage
to what already exists.

.. rubric:: Retrieve

Obtain information for a given Digi-Key part number :

>>> p = digikey.DigiKeyElnPart('800-2146-ND')
>>> p.manufacturer
'IDT, Integrated Device Technology Inc'
>>> p.mpartno
'72V2113L10PFI'
>>> p.vqtyavail
185
>>> p.datasheet
'http://www.idt.com/document/72v2103-72v2113-datasheet'
>>> p.package
'80-LQFP'
>>> p.vpartdesc
'IC FIFO SUPERSYNCII 10NS 80TQFP'

The pricing information is also populated by this time, and
can be accessed though the part object using the interfaces
defined in those class definitions.

>>> for b in p._prices:
...     print b
...
<VendorPrice INR 7,610.18 @1(1)>
<VendorPrice INR 6,801.37 @25(1)>
<VendorPrice INR 6,420.86 @100(1)>
<VendorPrice INR 6,183.05 @250(1)>
<VendorPrice INR 6,087.93 @500(1)>
<VendorPrice INR 5,802.56 @1000(1)>
<VendorPrice INR 5,707.43 @2500(1)>

Additionally, the contents of the Overview and Attributes
tables are available, though not parsed, in the form of BS4
trees. Note, however, that these contents are only available
when part details are obtained from the soup itself, and not
when reconstructed from the Tendril database.

>>> for k in p.attributes_table.keys():
...     print k
...
Category
Operating Temperature
Memory Size
Package / Case
Function
Product Photos
Datasheets
Current - Supply (Max)
Data Rate
Programmable Flags Support
FWFT Support
Standard Package
Bus Directional
Access Time
Online Catalog
Expansion Type
Family
Mounting Type
Series
Supplier Device Package
Packaging
Voltage - Supply
Other Names
Retransmit Capability

>>> for k in p.overview_table.keys():
...     print k
...
Description
Digi-Key Part Number
Manufacturer Part Number
Moisture Sensitivity Level (MSL)
Lead Free Status / RoHS Status
Quantity Available
Manufacturer
Price Break


"""

import locale
import re
import os
import urllib
import urlparse
from decimal import Decimal
import traceback
import csv
import codecs
from collections import namedtuple

from .vendors import SearchResult
from .vendors import VendorElnPartBase
from .vendors import VendorPrice
from .vendors import VendorBase
from . import customs

from tendril.utils import www
from tendril.utils.types import currency

from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import parse_resistor
from tendril.conventions.electronics import parse_capacitor
from tendril.conventions.electronics import parse_crystal
from tendril.conventions.electronics import check_for_std_val

from tendril.utils.config import INSTANCE_ROOT

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
SearchPart = namedtuple('SearchPart', 'pno, mfgpno, package, ns, unitp,  minqty')


class DigiKeyElnPart(VendorElnPartBase):
    def __init__(self, dkpartno, ident=None, vendor=None):
        """

        :type vendor: VendorDigiKey
        """
        if vendor is None:
            vendor = dvobj
        super(DigiKeyElnPart, self).__init__(dkpartno, ident, vendor)
        if not self._vpno:
            logger.error("Not enough information to create a Digikey Part")
        self._get_data()

    def _get_data(self):
        url = ('http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name=' +  # noqa
               urllib.quote_plus(self.vpno))
        soup = www.get_soup(url)
        if soup is None:
            logger.error("Unable to open DigiKey product page : " + self.vpno)
            return

        for price in self._get_prices(soup):
            self.add_price(price)

        self.overview_table = self._get_overview_table(soup)
        self.attributes_table = self._get_attributes_table(soup)

        self.manufacturer = self._get_manufacturer()
        self.mpartno = self._get_mpartno()
        self.datasheet = self._get_datasheet()
        self.package = self._get_package()
        self.vqtyavail = self._get_vqtyavail()
        self.vpartdesc = self._get_vpartdesc()

    def _get_prices(self, soup):
        pricingtable = soup.find('table', id='product-dollars')
        prices = []
        try:
            for row in pricingtable.findAll('tr'):
                cells = row.findAll('td')
                if len(cells) == 3:
                    cells = [cell.text.strip() for cell in cells]
                    if cells[0] == 'Call' and cells[1] == 'Call':
                        continue
                    try:
                        moq = locale.atoi(cells[0])
                    except ValueError:
                        moq = 0
                        logger.error(
                            cells[0] + " found while acquiring moq for " +
                            self.vpno
                        )
                    try:
                        price = locale.atof(cells[1])
                    except ValueError:
                        price = 0
                        logger.error(
                            cells[1] + " found while acquiring price for " +
                            self.vpno
                        )
                    prices.append(
                        VendorPrice(moq, price, self._vendor.currency)
                    )
        except AttributeError:
            logger.error(
                "Pricing table not found or other error for " + self.vpno
            )
        return prices

    @staticmethod
    def _get_table(table):
        rows = table.findAll('tr')
        parsed_rows = {}
        for row in rows:
            try:
                head = row.find('th').text.strip().encode('ascii', 'replace')
                data = row.find('td')
                parsed_rows[head] = data
            except AttributeError:
                continue
        return parsed_rows

    def _get_overview_table(self, soup):
        table = soup.find('table', {'id': 'product-details'})
        return self._get_table(table)

    def _get_attributes_table(self, soup):
        table = soup.find('table', {'class': 'attributes-table-main'})
        return self._get_table(table)

    def _get_mpartno(self):
        cell = self.overview_table['Manufacturer Part Number']
        return cell.text.strip().encode('ascii', 'replace')

    def _get_manufacturer(self):
        cell = self.overview_table['Manufacturer']
        return cell.text.strip().encode('ascii', 'replace')

    def _get_package(self):
        try:
            cell = self.attributes_table['Package / Case']
        except KeyError:
            return None
        return cell.text.strip().encode('ascii', 'replace')

    def _get_datasheet(self):
        try:
            cell = self.attributes_table['Datasheets']
        except KeyError:
            return None
        datasheet_link = cell.findAll('a')[0].attrs['href']
        return datasheet_link.strip()

    _regex_vqtyavail = re.compile(r'^Digi-Key Stock: (?P<qty>\d+(,*\d+)*)')
    _regex_vqty_vai = re.compile(r'^Value Added Item')

    def _get_vqtyavail(self):
        cell = self.overview_table['Quantity Available']
        text = cell.text.strip().encode('ascii', 'replace')
        try:
            m = self._regex_vqtyavail.search(text)
            qtytext = m.groupdict()['qty'].replace(',', '')
            return int(qtytext)
        except:
            if self._regex_vqty_vai.match(text):
                return -2
            return -1

    def _get_vpartdesc(self):
        cell = self.overview_table['Description']
        return cell.text.strip().encode('ascii', 'replace')


class DigiKeyInvoice(customs.CustomsInvoice):
    def __init__(self, vendor=None, inv_yaml=None, working_folder=None):
        if vendor is None:
            vendor = VendorDigiKey('digikey', 'Digi-Key Corporation',
                                   'electronics',
                                   currency_code='USD', currency_symbol='US$')
        if inv_yaml is None:
            inv_yaml = os.path.join(INSTANCE_ROOT, 'scratch', 'customs',
                                    'inv_data.yaml')

        super(DigiKeyInvoice, self).__init__(vendor, inv_yaml, working_folder)

    def _acquire_lines(self):
        logger.info("Acquiring Lines")
        invoice_file = os.path.join(self._source_folder,
                                    self._data['invoice_file'])
        with open(invoice_file) as f:
            reader = csv.reader(f)
            header = None
            for line in reader:
                if line[0].startswith(codecs.BOM_UTF8):
                    line[0] = line[0][3:]
                if line[0] == 'Index':
                    header = line
                    break
            if header is None:
                raise ValueError
            for line in reader:
                if line[0] != '':
                    idx = line[header.index('Index')].strip()
                    qty = int(line[header.index('Quantity')].strip())
                    vpno = line[header.index('Part Number')].strip()
                    desc = line[header.index('Description')].strip()
                    ident = line[header.index('Customer Reference')].strip()
                    boqty = line[header.index('Backorder')].strip()
                    try:
                        if int(boqty) > 0:
                            logger.warning(
                                "Apparant backorder. Crosscheck customs treatment for: " +  # noqa
                                idx + ' ' + ident
                            )
                    except ValueError:
                        print line

                    unitp_str = line[header.index('Unit Price')].strip()

                    unitp = currency.CurrencyValue(
                        float(unitp_str), self._vendor.currency
                    )
                    lineobj = customs.CustomsInvoiceLine(
                        self, ident, vpno, unitp, qty, idx=idx, desc=desc
                    )
                    self._lines.append(lineobj)


class VendorDigiKey(VendorBase):
    _partclass = DigiKeyElnPart
    _invoiceclass = DigiKeyInvoice

    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None):
        self._devices = ['IC SMD',
                         'IC THRU',
                         'IC PLCC',
                         'FERRITE BEAD SMD',
                         'TRANSISTOR THRU',
                         'TRANSISTOR SMD',
                         'CONN DF13',
                         'CONN DF13 HOUS',
                         'CONN DF13 WIRE',
                         'CONN DF13 CRIMP',
                         'CONN MODULAR',
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
        self._ndevices = ['CONN INTERBOARD']
        self._searchpages_filters = {}
        super(VendorDigiKey, self).__init__(
            name, dname, pclass, mappath, currency_code, currency_symbol
        )
        self._vpart_class = DigiKeyElnPart
        self.add_order_baseprice_component("Shipping Cost", 40)
        self.add_order_additional_cost_component("Customs", 12.85)

    def search_vpnos(self, ident):
        device, value, footprint = parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if device.startswith('RES') or device.startswith('POT') or \
                    device.startswith('CAP') or device.startswith('CRYSTAL'):
                if check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value, footprint)
                try:
                    return None, 'NODEVICE'
                    return self._get_pas_vpnos(device, value, footprint)
                except NotImplementedError:
                    logger.warning(ident + ' :: DK Search for ' + device +
                                   ' Not Implemented')
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
    def _search_preprocess(device, value, footprint):
        if footprint == 'TO220':
            footprint = 'TO-220'
        if footprint == 'TO92':
            footprint = 'TO-92'
        return device, value, footprint

    @staticmethod
    def _process_product_page(soup):
        beablock = soup.find('div', {'class': 'product-details-feedback'})
        if beablock is not None:
            if beablock.text == u'\nObsolete item; call Digi-Key for more information.\n':  # noqa
                return SearchResult(False, None, 'OBSOLETE_NOTAVAIL')
        pdtable = soup.find('table', {'id': 'product-details'})
        if pdtable is not None:
            pno_meta = pdtable.find('meta', {'itemprop': 'productID'})
            if pno_meta is None:
                return SearchResult(False, None, 'NO_PNO_CELL')
            pno_text = pno_meta.attrs['content']
            pno = pno_text.split(':')[1].encode('ascii', 'replace')

            mpno_meta = pdtable.find('meta', {'itemprop': 'name'})
            mpno_text = mpno_meta.attrs['content']
            mpno = mpno_text.encode('ascii', 'replace')

            # TODO
            # The current approach of handling catergories and subcategories
            # can result in these seemingly 'exact match' results to be put
            # into a comparison. If that were to happen, the Package/Case,
            # Unit Price, and MOQ are all necessary pieces of information to
            # determine inclusion. These should be handled here, and
            # preferably without instantiating a full digikey part instance.
            part = {'Digi-Key Part Number': pno,
                    'Manufacturer Part Number': mpno,
                    'Package / Case': 'Dummy',
                    'Unit Price (USD)': '100',
                    'Minimum Quantity': '1'}
            return SearchResult(True, [part], 'EXACT_MATCH')
        else:
            return SearchResult(False, None, 'NO_PDTABLE')

    @staticmethod
    def _get_device_catstrings(device):
        if device.startswith('IC'):
            catstrings = ['Integrated Circuits (ICs)',
                          'Isolators']
        elif device.startswith('DIODE'):
            catstrings = ['Discrete Semiconductor Products']
        elif device.startswith('TRANSISTOR'):
            catstrings = ['Discrete Semiconductor Products']
        elif device.startswith('BRIDGE RECTIFIER'):
            catstrings = ['Discrete Semiconductor Products']
        else:
            return False, None
        return True, catstrings

    @staticmethod
    def _get_device_subcatstrings(device):
        if device.startswith('IC'):
            subcatstrings = ['Interface - Controllers']
        elif device.startswith('DIODE'):
            subcatstrings = ['Diodes, Rectifiers - Single']
        elif device.startswith('TRANSISTOR'):
            subcatstrings = ['FETs - Single']
        elif device.startswith('BRIDGE RECTIFIER'):
            subcatstrings = ['Bridge Rectifiers']
        else:
            return False, None
        return True, subcatstrings

    def _process_secondary_index_page(self, soup, device):
        result, subcatstrings = self._get_device_subcatstrings(device)
        if subcatstrings is None or len(subcatstrings) == 0:
            return SearchResult(False, None, 'SUBCATEGORY_UNKNOWN')

        cathead = soup.find('h1', {'class': 'catfiltertopitem'})

        if cathead is None:
            return SearchResult(False, None, 'SECONDARY_INDEX_NOT_FOUND')

        subcatcontainer = soup.find('ul', {'id': 'catfiltersubid'})
        subcat_elems = subcatcontainer.findAll('a')
        subcats = {}

        for elem in subcat_elems:
            subcat_name = elem.text.strip().encode('ascii', 'replace')
            subcat_url_part = elem.attrs['href'].strip()
            subcats[subcat_name] = subcat_url_part

        new_url_parts = []
        for subcat_name in subcats.keys():
            if subcat_name in subcatstrings:
                new_url_parts.append(subcats[subcat_name])

        if len(new_url_parts) == 0:
            return SearchResult(False, None, 'SUBCATEGORY_NOT_FOUND')

        results = []
        for url_part in new_url_parts:
            new_url = urlparse.urljoin('http://www.digikey.com', url_part)
            soup = www.get_soup(new_url)
            if soup is not None:
                try:
                    results.extend(self._get_resultpage_table(soup))
                except ValueError:
                    # Must be a product page
                    sr = self._process_product_page(soup)
                    if sr.success is True:
                        results.extend(sr.parts)
        if len(results):
            return SearchResult(True, results, '')
        else:
            return SearchResult(False, [], 'SECONDARY_INDEX_TRAVERSAL')

    def _process_index_page(self, soup, device):
        idxlist = soup.find('div', id='productIndexList')
        if idxlist is None:
            return SearchResult(False, None, 'INDEX_NOT_FOUND')
        # Handling categories needs to be much better
        catheads = idxlist.findAll('h2', attrs={'class': 'catfiltertopitem'})
        cats = {}
        for cat in catheads:
            cat_elem = cat.find('a')
            cat_name = cat_elem.text.strip().encode('ascii', 'replace')
            cat_url_part = cat_elem.attrs['href'].strip()
            cats[cat_name] = cat_url_part

        result, catstrings = self._get_device_catstrings(device)
        if result is False:
            return SearchResult(False, None, 'CATEGORY_UNKNOWN')

        new_url_parts = []
        for cat_name in cats.keys():
            if cat_name in catstrings:
                new_url_parts.append(cats[cat_name])

        if len(new_url_parts) == 0:
            return SearchResult(False, None, 'CATEGORY_NOT_FOUND')

        results = []
        for url_part in new_url_parts:
            new_url = urlparse.urljoin('http://www.digikey.com', url_part)
            soup = www.get_soup(new_url)
            if soup is not None:
                try:
                    results.extend(self._get_resultpage_table(soup))
                except ValueError:
                    # Either an exact match or a secondary index
                    sr = self._process_product_page(soup)
                    if sr.success is True:
                        results.extend(sr.parts)
                        continue
                    if sr.strategy == 'NO_PDTABLE':
                        sr = self._process_secondary_index_page(soup, device)
                        if sr.success is True:
                            results.extend(sr.parts)
        if len(results):
            return SearchResult(True, results, '')
        else:
            return SearchResult(False, [], 'INDEX_TRAVERSAL')

    @staticmethod
    def _process_resultpage_row(row):
        """
        Given a 'row' from a CSV file obtained from Digi-Key's search
        interface and read in using ``csv.DictReader``, convert it into
        a ``SearchPart`` instance.

        If the unit price for the row is not readily parseable into a
        float, or if the minqty field includes a Non-Stock note, the
        returned SearchPart has it's `ns` attribute set to True.

        :type row: dict
        :rtype: ``SearchPart``
        """
        pno = row.pop('Digi-Key Part Number', '').strip()
        package = row.pop('Package / Case', '').strip()
        minqty = row.pop('Minimum Quantity', '').strip()
        mfgpno = row.pop('Manufacturer Part Number', '').strip()
        unitp = row.pop('Unit Price (USD)', '').strip()
        try:
            unitp = locale.atof(unitp)
        except ValueError:
            unitp = None
        if pno is not None:
            if 'Non-Stock' in minqty or unitp is None:
                ns = True
            else:
                ns = False
        else:
            ns = True
        part = SearchPart(pno=pno, mfgpno=mfgpno, package=package,
                          ns=ns, unitp=unitp,  minqty=minqty)
        return part

    def _get_resultpage_parts(self, rows):
        parts = []
        for row in rows:
            part = self._process_resultpage_row(row)
            parts.append(part)
        return SearchResult(True, parts, '')

    @staticmethod
    def _filter_results_unfiltered(parts):
        """
        Given a list of ``SearchPart`` instances, returns a ``SearchResult``
        instance, whose 'parts' attribute includes a list of part numbers.

        If any of the part numbers are not listed as Non-Stocked, then only
        the Stocked results are returned along with the strategy 'UNFILTERED'.

        If all of the part numbers are listed as Non-Stocked, then all the
        part numbers are returned with the strategy 'UNFILTERED_ALLOW_NS'.

        :type parts: ``list`` of ``SearchPart``
        :rtype: ``SearchResult``
        """
        pnos = []
        strategy = 'UNFILTERED'
        for part in parts:
            if not part.ns:
                pnos.append(part.pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for part in parts:
                pnos.append(part.pno)
        return SearchResult(True, pnos, strategy)

    @staticmethod
    def _find_exact_match_package(parts, value):
        """
        Given a list of ``SearchPart`` instances and a known value, returns
        a ``SearchResult`` instance, whose 'parts' attribute includes only
        the package of the part whose manufacturer part number (mfgpno)
        exactly matches the given value, if such an exact match can be found.

        The ``SearchResult`` returned on success has it's strategy attribute
        set to `EXACT_MATCH_FFP`.

        :type parts: ``list`` of ``SearchPart``
        :type value: str
        :rtype: ``SearchResult``
        """
        for part in parts:
            if part.mfgpno == value:
                return SearchResult(True, part.package, 'EXACT_MATCH_FFP')
        return SearchResult(False, None, None)

    @staticmethod
    def _find_consensus_package(parts):
        """
        Given a list of ``SearchPart`` instances, returns a ``SearchResult``
        instance, whose 'parts' attribute includes only the consensus package
        of all the parts in the provided list, if such a consensus can be
        reached.

        The ``SearchResult`` returned on success has it's strategy attribute
        set to `CONSENSUS_FP_MATCH`.

        :type parts: ``list`` of ``SearchPart``
        :rtype: ``SearchResult``
        """
        cpackage = parts[0].package
        for part in parts:
            if part.package != cpackage:
                cpackage = None
        if cpackage is not None:
            return SearchResult(True, cpackage, 'CONSENSUS_FP_MATCH')
        return SearchResult(False, None, None)

    @staticmethod
    def _filter_results_byfootprint(parts, footprint):
        """
        Given a list of ``SearchPart`` instances and the target footprint,
        returns a ``SearchResult`` instance, whose 'parts' attribute
        includes part numbers for all parts in the provided list whose
        package attribute contains the provided footprint.

        This is a last ditch effort. Due to the diversity in package
        nomenclature, this has a very low likelihood of success
        without an exceptionally well curated symbol library. The
        ``SearchResult`` returned on success has it's strategy attribute
        set to `HAIL_MARY` or `HAIL_MARY_ALLOW_NS`.

        :type parts: ``list`` of ``SearchPart``
        :type footprint: str
        :rtype: ``SearchResult``
        """
        pnos = []
        strategy = 'HAIL MARY'
        for part in parts:
            if footprint in part.package:
                if not part.ns:
                    pnos.append(part.pno)
        if len(pnos) == 0:
            strategy += ' ALLOW NS'
            for part in parts:
                if footprint in part.package:
                    pnos.append(part.pno)
        return SearchResult(True, pnos, strategy)

    @staticmethod
    def _filter_results_bycpackage(parts, cpackage, strategy):
        """
        Given a list of ``SearchPart`` instances, and a consensus package
        string, returns a ``SearchResult`` instance, whose 'parts' attribute
        includes the part numbers of all the parts in the provided list whose
        package attribute matches the consensus package.

        When used in the correct context, this function uses cpackage instead
        of the original footprint. cpackage is itself extracted from the
        result table, and therefore greatly decreases (though not eliminates)
        the odds of false negatives.

        A strategy is accepted as the third argument to this function, and is
        returned within the ``SearchResult``, with modification to append
        `_ALLOW_NS` if necessary.

        :type parts: ``list`` of ``SearchPart``
        :param cpackage: A consensus or exact match package.
        :type cpackage: str
        :type strategy: str
        :rtype: ``SearchResult``
        """
        pnos = []
        for part in parts:
            if part.package == cpackage:
                if not part.ns:
                    pnos.append(part.pno)
        if len(pnos) == 0:
            strategy += '_ALLOW_NS'
            for part in parts:
                if part.package == cpackage:
                    pnos.append(part.pno)
        return SearchResult(True, pnos, strategy)

    def _filter_results(self, parts, value, footprint):
        if parts[0].package is None or footprint is None:
            # No package, so no basis to filter
            sr = self._filter_results_unfiltered(parts)
            return SearchResult(True, sr.parts, sr.strategy)

        # Find Exact Match Package
        sr = self._find_exact_match_package(parts, value)
        cpackage = sr.parts
        strategy = sr.strategy
        if sr.success is False:
            # Did not find an exact match package.
            # Check for consensus package instead.
            sr = self._find_consensus_package(parts)
            cpackage = sr.parts
            strategy = sr.strategy
            if sr.success is False:
                # No exact match, no consensus on package
                sr = self._filter_results_byfootprint(parts, footprint)
                return SearchResult(True, sr.parts, sr.strategy)

        # cpackage exists
        sr = self._filter_results_bycpackage(parts, cpackage, strategy)

        if len(sr.parts) == 0:
            pnos = None
        else:
            pnos = sr.parts

        return SearchResult(True, pnos, sr.strategy)

    @staticmethod
    def _remove_duplicates(parts):
        vpnos = []
        for part in parts:
            if part.pno in vpnos:
                parts.pop(part)
            else:
                vpnos.append(part.pno)
        return parts

    def _process_results(self, parts, value, footprint):
        parts = self._remove_duplicates(parts)
        return self._filter_results(parts, value, footprint)

    @staticmethod
    def _get_resultpage_table(soup):
        form = soup.find('form', {'name': 'downloadform'})
        if form is None:
            raise ValueError
        params = []
        parts = form.findAll('input')
        for part in parts:
            params.append((part.attrs['name'], part.attrs['value']))

        url_base = 'http://www.digikey.com/'
        target = urlparse.urljoin(url_base, form.attrs['action'])
        url_dl = target + '?' + urllib.urlencode(params)

        # TODO
        # Trying to do this normaly, with returned data, results in
        # horribly convoluted encoding errors. A great deal of streamlining
        # of encoding across the stack may be necessary to make this work
        # reliably. For now, we reopen the cache file which seems to have a
        # stable encoding, though an encoding which is different from or
        # incorrectly marked when compared to that provided by the stream.
        table_csv_path = www.cached_fetcher.fetch(url_dl, getcpath=True)
        with codecs.open(table_csv_path, 'r', encoding='utf-8') as f:
            table_csv = f.read()
        table_csv = table_csv.encode('utf-8')

        if table_csv.startswith(codecs.BOM_UTF8):
            table_csv = table_csv[len(codecs.BOM_UTF8):]

        lines = csv.DictReader(table_csv.splitlines())
        return lines

    def _get_search_vpnos(self, device, value, footprint):
        if value.strip() == '':
            return None, 'NOVALUE'
        device, value, footprint = self._search_preprocess(
            device, value, footprint
        )
        url = 'http://www.digikey.com/product-search/en?k=' + \
              urllib.quote_plus(value) + \
              '&mnonly=0&newproducts=0&ColumnSort=0&page=1&stock=0&pbfree=0&rohs=0&quantity=&ptm=0&fid=0&pageSize=500'  # noqa
        soup = www.get_soup(url)
        if soup is None:
            return None, 'URL_FAIL'
        ptable = soup.find('table', id='productTable')
        index_results = None
        if ptable is None:
            # check for single product page
            sr = self._process_product_page(soup)
            if sr.success is True:
                # Sent directly to an exact match. Just send it back.
                return [sr.parts[0]['Digi-Key Part Number']], sr.strategy

            # check for secondary index page and get full parts listing
            # thereof
            sr = self._process_secondary_index_page(soup, device)
            if sr.success is True:
                index_results = sr.parts
            elif sr.strategy == 'SECONDARY_INDEX_NOT_FOUND':
                # No secondary index there
                # check for index page and get full parts listing thereof
                sr = self._process_index_page(soup, device)
                if sr.success is False:
                    # No luck with the index
                    return None, sr.strategy
                index_results = sr.parts
            else:
                return None, sr.strategy

        if index_results is None:
            table = self._get_resultpage_table(soup)
        else:
            table = index_results

        sr = self._get_resultpage_parts(table)
        if sr.success is False:
            return SearchResult(False, None, sr.strategy)
        if sr.parts is None:
            raise Exception
        if len(sr.parts) == 0:
            return SearchResult(False, None, 'NO_RESULTS:2')

        results = sr.parts
        sr = self._process_results(results, value, footprint)
        if sr.success is False:
            return None, sr.strategy
        return sr.parts, sr.strategy

    @staticmethod
    def _tf_resistance_to_canonical(rstr):
        rstr = rstr.encode('ascii', 'replace')
        rex = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[kKMGT])*$')
        try:
            rparts = rex.search(rstr).groupdict()
        except AttributeError:
            print rstr
            raise AttributeError

        rval = Decimal(rparts['num'])
        if rparts['order'] is None:
            do = 0
            if rval > 1000:
                raise ValueError
            while 1 > rval > 0:
                rval *= 1000
                do += 1
            if do == 0:
                ostr = 'E'
            elif do == 1:
                ostr = 'm'
            elif do == 2:
                ostr = 'u'
            else:
                raise ValueError
        else:
            if rparts['order'] in ['K', 'k']:
                ostr = 'K'
            elif rparts['order'] == 'M':
                ostr = 'M'
            elif rparts['order'] == 'G':
                ostr = 'G'
            elif rparts['order'] == 'T':
                ostr = 'T'
            else:
                raise ValueError(str(rparts))
        vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())  # noqa
        return vfmt(rval) + ostr

    @staticmethod
    def _tf_tolerance_to_canonical(tstr):
        tstr = www.strencode(tstr)
        return tstr

    @staticmethod
    def _tf_capacitance_to_canonical(cstr):
        cstr = www.strencode(cstr)
        if cstr == '-':
            return
        if cstr == '*':
            return
        rex = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[pum]F)$')

        try:
            cparts = rex.search(cstr).groupdict()
        except AttributeError:
            raise AttributeError(cstr)

        cval = Decimal(cparts['num'])

        ostr = cparts['order']
        ostrs = ['fF', 'pF', 'nF', 'uF', 'mF']
        oindex = ostrs.index(ostr)

        if cparts['order'] is None:
            raise ValueError
        if cval >= 1000:
            po = 0
            while cval >= 1000:
                cval /= 1000
                po += 1
            if po > 0:
                for i in range(po):
                    oindex += 1
        else:
            do = 0
            while 0 < cval < 1:
                cval *= 1000
                do += 1
            if do > 0:
                for i in range(do):
                    oindex -= 1

        vfmt = lambda d: str(d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize())  # noqa
        return vfmt(cval) + ostrs[oindex]

    @staticmethod
    def _tf_package_tant_smd(footprint):
        if footprint == 'TANT-B':
            footprint = 'B'
        if footprint == 'TANT-C':
            footprint = 'C'
        if footprint == 'TANT-D':
            footprint = 'D'
        return footprint

    @staticmethod
    def _tf_package_crystal_at(footprint):
        if footprint == 'HC49':
            footprint = ['HC-49S', 'HC49/U', 'HC49/US']
        return footprint

    def _get_searchpage_filters(self, soup):
        filters = {}
        try:
            filtertable = soup.find('table', attrs={'class': 'filters-group'})
            headers = filtertable.find('tr')
            headers = [header.text.encode('ascii', 'replace')
                       for header in headers.findAll('th')]
            fvaluerow = filtertable.findAll('tr')[1]
            fvaluecells = fvaluerow.findAll('td')
            fvalueselects = [cell.find('select') for cell in fvaluecells]
            for idx, header in enumerate(headers):
                optionsoup = fvalueselects[idx].findAll('option')
                options = [(www.strencode(o.text).rstrip('\n'),
                            o.attrs['value']) for o in optionsoup]
                fname = fvalueselects[idx].attrs['name'].encode('ascii',
                                                                'replace')
                if header == 'Resistance (Ohms)':
                    options = [(self._tf_resistance_to_canonical(option[0]), option[1]) for option in options]  # noqa
                elif header == 'Capacitance':
                    options = [(self._tf_capacitance_to_canonical(option[0]), option[1]) for option in options]  # noqa
                elif header == 'Tolerance':
                    options = [(self._tf_tolerance_to_canonical(option[0]), option[1]) for option in options]  # noqa
                filters[header] = (fname, options)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('idx :' + str(idx))
            return False, None
        return True, filters

    @staticmethod
    def _get_default_urlparams():
        params = [('stock', '0'), ('mnonly', '0'), ('newproducts', '0'),
                  ('ColumnSort', '0'), ('page', '1'), ('quantity', '0'),
                  ('ptm', '0'), ('fid', '0'), ('pagesize', '500')]
        return params

    @staticmethod
    def _get_searchurl_res_smd():
        return 'http://www.digikey.com/product-search/en/resistors/chip-resistor-surface-mount/'  # noqa

    @staticmethod
    def _get_searchurl_res_thru():
        return 'http://www.digikey.com/product-search/en/resistors/through-hole-resistors/'  # noqa

    @staticmethod
    def _get_searchurl_cap_cer_smd():
        return 'http://www.digikey.com/product-search/en/capacitors/ceramic-capacitors/'  # noqa

    @staticmethod
    def _get_searchurl_cap_tant_smd():
        return 'http://www.digikey.com/product-search/en/capacitors/tantalum-capacitors/'  # noqa

    @staticmethod
    def _get_searchurl_crystal():
        return 'http://www.digikey.com/product-search/en/crystals-and-oscillators/crystals/'  # noqa

    def _get_searchurl_filters(self, searchurl):
        if searchurl in self._searchpages_filters.keys():
            return self._searchpages_filters[searchurl]
        else:
            searchsoup = www.get_soup(searchurl)
            result, filters = self._get_searchpage_filters(searchsoup)
            if result is True:
                self._searchpages_filters[searchurl] = filters
            else:
                raise AttributeError
        return filters

    def _get_pas_vpnos(self, device, value, footprint):
        packagetf = None
        package_header = 'Package / Case'
        package_filter_type = 'contains'
        extraparams = None
        if device == "RES SMD":
            filters = self._get_searchurl_filters(
                self._get_searchurl_res_smd()
            )
            searchurlbase = self._get_searchurl_res_smd()
            devtype = 'resistor'
        elif device == "RES THRU":
            filters = self._get_searchurl_filters(
                self._get_searchurl_res_thru()
            )
            searchurlbase = self._get_searchurl_res_thru()
            extraparams = (('Tolerance', '+/-1%'),)
            package_filter_type = None
            devtype = 'resistor'
        elif device == "RES POWER":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES ARRAY THRU":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES SMD THRU":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "POT TRIM":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "CAP CER SMD":
            filters = self._get_searchurl_filters(
                self._get_searchurl_cap_cer_smd()
            )
            searchurlbase = self._get_searchurl_cap_cer_smd()
            devtype = 'capacitor'
        elif device == "CAP TANT SMD":
            filters = self._get_searchurl_filters(
                self._get_searchurl_cap_tant_smd()
            )
            packagetf = self._tf_package_tant_smd
            searchurlbase = self._get_searchurl_cap_tant_smd()
            package_header = 'Manufacturer Size Code'
            package_filter_type = 'equals'
            devtype = 'capacitor'
        elif device == "CAP CER THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP ELEC THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP ELEC THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP POLY THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CAP PAPER THRU":
            devtype = 'capacitor'
            raise NotImplementedError
        elif device == "CRYSTAL AT":
            filters = self._get_searchurl_filters(
                self._get_searchurl_crystal()
            )
            packagetf = self._tf_package_crystal_at
            package_filter_type = 'inlist'
            searchurlbase = self._get_searchurl_crystal()
            extraparams = (('Mounting Type', 'Through Hole'),
                           ('Operating Mode', 'Fundamental'))
            devtype = 'crystal'
        else:
            raise ValueError

        if devtype == 'resistor':
            loptions = (('resistance', "Resistance (Ohms)", 'equals'),
                        ('wattage', "Power (Watts)", 'contains'))
            lvalues = parse_resistor(value)
        elif devtype == 'capacitor':
            loptions = (('capacitance', "Capacitance", 'equals'),
                        ('voltage', "Voltage - Rated", 'equals'))
            lvalues = parse_capacitor(value)
        elif devtype == 'crystal':
            loptions = (('frequency', "Frequency", 'equals'),)
            lvalues = [parse_crystal(value)]
        else:
            raise ValueError

        params = self._get_default_urlparams()

        for lidx, loption in enumerate(loptions):
            if lvalues[lidx] is None:
                continue
            dkopcode = None

            for option in filters[loption[1]][1]:
                if loption[2] == 'equals':
                    if option[0] == lvalues[lidx]:
                        dkopcode = option[1]
                elif loption[2] == 'contains':
                    if lvalues[lidx] in option[0]:
                        dkopcode = option[1]
            dkfiltcode = filters[loption[1]][0]
            if dkopcode is None:
                raise ValueError(loption[0] + ' ' + lvalues[lidx])
            params.append((dkfiltcode, dkopcode))

        if packagetf is not None:
            footprint = packagetf(footprint)
        if package_filter_type is not None:
            pkgopcode = None
            for option in filters[package_header][1]:
                if package_filter_type == 'contains':
                    if footprint in option[0]:
                        pkgopcode = option[1]
                elif package_filter_type == 'equals':
                    if footprint == option[0]:
                        pkgopcode = option[1]
                elif package_filter_type == 'inlist':
                    if option[0] in footprint:
                        try:
                            pkgopcode.append(option[1])
                        except AttributeError:
                            pkgopcode = [option[1]]
            if pkgopcode is None:
                raise ValueError(footprint)
            if isinstance(pkgopcode, list):
                for opt in pkgopcode:
                    params.append((filters[package_header][0], opt))
            else:
                params.append((filters[package_header][0], pkgopcode))

        if extraparams is not None:
            for param in extraparams:
                opcode = None
                for option in filters[param[0]][1]:
                    if option[0] == param[1]:
                        opcode = option[1]
                if opcode is None:
                    for option in filters[param[0]][1]:
                        print option[0].decode('unicode-escape')
                    raise ValueError("Param not valid: " + str(param))
                params.append((filters[param[0]][0], opcode))

        searchurl = searchurlbase + '?' + urllib.urlencode(params)

        soup = www.get_soup(searchurl)
        # TODO extract common parts with _get_search_vpnos
        if soup is None:
            return None, 'URL_FAIL'

        ptable = soup.find('table', id='productTable')
        if ptable is None:
            # check for single product page
            result, pnos, strategy = self._process_product_page(soup)
            if result is True:
                return pnos, strategy
            else:
                return None, strategy

        result, pnos, strategy = self._process_results_page(soup, None, None)
        if result is False:
            return None, strategy
        return pnos, strategy


dvobj = VendorDigiKey('digikey', 'Digi-Key Corporation',
                      'electronics', mappath=None,
                      currency_code='USD', currency_symbol='US$')
