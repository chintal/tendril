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
Digi-Key Vendor Module (:mod:`tendril.sourcing.digikey`)
========================================================

'Standalone' Usage
------------------

This module can be imported by itself to provide limited but potentially
useful functionality.

>>> from tendril.sourcing import digikey

.. rubric:: Search

Search for Digi-Key part numbers given a Tendril-compatible ident string :

>>> digikey.dvobj.search_vpnos('IC SMD W5300 LQFP100-14')
(['1278-1009-ND'], 'EXACT_MATCH_FFP')

>>> digikey.dvobj.search_vpnos('IC SMD LM311 8-TSSOP')
(['296-13719-2-ND', '296-13719-1-ND'], 'NAIVE_FP_MATCH')

Note that only certain types of components are supported by the search. The
``device`` component of the ident string is used to determine whether or not
a search will even be attempted. See :data:`VendorDigiKey._devices` for a
list of supported device classes. For all device classes, search is
supported only for components whose ``value`` is a manufacturer part number,
or enough of one to sufficiently identify the part in question.

.. seealso::
    :ref:`symbol-conventions`

For certain (very specific) device classes, the search can be done using
generic descriptions of the component. These 'jelly bean' components must
have a correctly formatted ``value``, as per the details listed in the
:ref:`symbol-conventions`.

>>> digikey.dvobj.search_vpnos('CAP CER SMD 22uF/35V 0805')
(['445-14428-2-ND', '445-14428-1-ND', '445-11527-2-ND', '445-11527-1-ND'],
 'CONSENSUS_FP_MATCH')

>>> digikey.dvobj.search_vpnos('RES SMD 1.15E/0.125W 0805')
(['311-1.15CRTR-ND', '311-1.15CRCT-ND', '541-1.15CCTR-ND', '541-1.15CCCT-ND'],
'CONSENSUS_FP_MATCH')

>>> digikey.dvobj.search_vpnos('RES ARRAY SMD 102E/0.0625W 1206-4')
(['TC164-FR-07102RL-ND', 'AF164-FR-07102RL-ND'], 'NAIVE_FP_MATCH_ALLOW_NS')

>>> digikey.dvobj.search_vpnos('CRYSTAL AT 13MHz HC49')
(['887-2036-ND'], 'EXACT_MATCH')


.. seealso::
    Implementation of :func:`VendorDigiKey._get_pas_vpnos` and the
    functions that it uses to perform this search.

Even with supported device types, remember that this search is nowhere near
bulletproof. The more generic a device and/or its name is, the less likely
it is to work. The intended use for this type of search is in concert with
an organization's engineering policies and an instance administrator who
can make the necessary tweaks to the search algortihms and maintain a low
error rate for component types commonly used within the instance.

.. seealso::
    :func:`VendorDigiKey._search_preprocess`
    :func:`VendorDigiKey._get_device_catstrings`
    :func:`VendorDigiKey._get_device_subcatstrings`
    :func:`VendorDigiKey._get_device_subcatstrings`

Tweaks and improvements to the search process are welcome as pull requests
to the tendril github repository, though their inclusion will be predicated
on them causing minimal breakage to what already exists.

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

The pricing information is also populated by this time, and can be accessed
though the part object using the interfaces defined in those class definitions.

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

.. hint::
    By default, the :class:`.vendors.VendorPrice` instances are represented
    by the unit price in the currency defined by the
    :data:`tendril.utils.types.currency.native_currency_defn`.

Additionally, the contents of the Overview and Attributes tables are
available, though not parsed, in the form of BS4 trees. Note, however, that
these contents are only available when part details are obtained from the
soup itself, and not when reconstructed from the Tendril database.

>>> for k in p.attributes_table.keys():
...     print(k)
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

import codecs
import csv
import locale
import os
import re
import traceback
import urllib
import urlparse
from copy import copy
from decimal import Decimal
from urllib2 import HTTPError

from tendril.conventions.electronics import check_for_std_val
from tendril.conventions.electronics import parse_capacitor
from tendril.conventions.electronics import parse_crystal
from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import parse_resistor
from tendril.utils import log
from tendril.utils import www
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.types import currency
from tendril.utils.types.electromagnetic import Capacitance
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import Voltage
from tendril.utils.types.thermodynamic import ThermalDissipation
from tendril.utils.types.time import Frequency
from . import customs
from .vendors import SearchPart
from .vendors import SearchResult
from .vendors import VendorBase
from .vendors import VendorElnPartBase
from .vendors import VendorPrice
from .vendors import VendorPartRetrievalError


logger = log.get_logger(__name__, log.DEFAULT)
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


class DigiKeyElnPart(VendorElnPartBase):
    def __init__(self, dkpartno, ident=None, vendor=None, max_age=-1):
        """
        This class acquires and contains information about a single DigiKey
        part number, specified by the `dkpartno` parameter.

        :param dkpartno: The DigiKey part number.
        :type dkpartno: str
        :param ident: ``(Optional)`` Allows the caller to include the
                      canonical representation within Tendril for the
                      part represented by the object. This is required
                      for use with the Tendril database.
        :type ident: str
        :param vendor: ``(Optional)`` Allows the caller to 'bind' the part
                       to the pre-existing vendor objects in Tendril's
                       sourcing infrastructure. This is required
                       for use with the Tendril database.
        :type vendor: :class:`VendorDigiKey`

        """
        if vendor is None:
            vendor = dvobj
        if not dkpartno:
            logger.error("Not enough information to create a Digikey Part")
        super(DigiKeyElnPart, self).__init__(dkpartno, ident, vendor, max_age)

    @property
    def vparturl(self):
        if self._vparturl:
            return self._vparturl
        else:
            return 'http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name=' \
                    + urllib.quote_plus(self.vpno)

    def _get_data(self):
        """
        This function downloads the part page from Digi-Key, scrapes the page,
        and populates the object with all the necessary information.

        """
        try:
            soup = self._vendor.get_soup(self.vparturl)
        except HTTPError as e:
            if e.code == 404:
                logger.error("Got 404 opening DigiKey product page : " + self.vpno)
                raise VendorPartRetrievalError
            else:
                raise
        if soup is None:
            logger.error("Unable to open DigiKey product page : " + self.vpno)
            raise VendorPartRetrievalError

        for price in self._get_prices(soup):
            self.add_price(price)

        try:
            self.overview_table = self._get_overview_table(soup)
        except AttributeError:
            logger.error("Error acquiring DigiKey information for {0}"
                         "".format(self.vpno))
            return
        self.attributes_table = self._get_attributes_table(soup)

        self.manufacturer = self._get_manufacturer()
        self.mpartno = self._get_mpartno()
        self.datasheet = self._get_datasheet()
        self.package = self._get_package()
        self.vqtyavail = self._get_vqtyavail()
        self.vpartdesc = self._get_vpartdesc()

    def _get_prices(self, soup):
        """
        Given the BS4 parsed soup of the Digi-Key product page, this function
        extracts the prices and breaks and returns them as a list of
        :class:`.vendors.VendorPrice` instances.

        Price listings containing only 'Call' are ignored. Any other
        non-numeric content for the price or break quantity listing results
        in an error message from the logger and the corresponding price /
        break quantity is returned as 0.

        """
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
                        moq = int(cells[0].replace(',', ''))
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
        """
        Parses tabular data in the format of Digi-Key's part detail tables,
        obtained from a BS4 parsed tree.

        The tables parsed are of the format :

        .. code-block:: html

            <table>
                ...
                <tr>
                    <th> [HEAD] </th>
                    <td> [DATA] </th>
                </tr>
                ...
            </table>

        The parsed table is returned as a dictionary. For each row in the
        table, the extracted ``[HEAD]`` is stripped, encoded to ascii and
        used as a key, and value is the corresponding ``[DATA]`` in it's
        BS4 parsed form.

        """
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
        """
        Given the BS4 parsed soup of the Digi-Key product page, this function
        extracts and returns the overview / product-detail table using
        :func:`_get_table`.
        """
        table = soup.find('table', {'id': 'product-details'})
        return self._get_table(table)

    def _get_attributes_table(self, soup):
        """
        Given the BS4 parsed soup of the Digi-Key product page, this function
        extracts and returns the product attributes table using
        :func:`_get_table`.
        """
        table = soup.find('table', {'class': 'attributes-table-main'})
        return self._get_table(table)

    def _get_mpartno(self):
        """
        Extracts the Manufacturer Part Number from the overview table.
        """
        cell = self.overview_table['Manufacturer Part Number']
        return cell.text.strip().encode('ascii', 'replace')

    def _get_manufacturer(self):
        """
        Extracts the Manufacturer from the overview table.
        """
        cell = self.overview_table['Manufacturer']
        return cell.text.strip().encode('ascii', 'replace')

    def _get_package(self):
        """
        Extracts the Package from the attributes table. If ``Package / Case``
        is not found in the table, returns None.
        """
        try:
            cell = self.attributes_table['Package / Case']
        except KeyError:
            return None
        return cell.text.strip().encode('ascii', 'replace')

    def _get_datasheet(self):
        """
        Extracts the first datasheet link from the attributes table.
        If ``Datasheets`` is not found in the table, returns None.
        """
        try:
            cell = self.attributes_table['Datasheets']
        except KeyError:
            return None
        datasheet_link = cell.findAll('a')[0].attrs['href']
        return datasheet_link.strip()

    _regex_vqtyavail = re.compile(r'^(?P<qty>\d+(,*\d+)*)\s*Can ship immediately')
    _regex_vqty_vai = re.compile(r'^Value Added Item')

    def _get_vqtyavail(self):
        """
        Extracts the Quantity Available from the overview table. If
        ``Value Added Item`` is found in the available quantity cell,
        returns -2. If any other non integral value is found in the
        cell, returns -1.
        """
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
        """
        Extracts the Description from the overview table.
        """
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
                                "Apparant backorder. Crosscheck customs "
                                "treatment for: {0} {1}".format(idx, ident)
                            )
                    except ValueError:
                        print(line)

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

    #: Supported Device Classes
    #:
    #: .. hint::
    #:      This handles instance-specific tweaks, and should be
    #:      modified to match your instance's nomenclature guidelines.
    #:
    _devices = [
        'IC SMD', 'IC THRU', 'IC PLCC',
        'FERRITE BEAD SMD', 'TRANSISTOR THRU', 'TRANSISTOR SMD', 'MOSFET SMD',
        'CONN DF13', 'CONN DF13 HOUS', 'CONN DF13 WIRE', 'CONN DF13 CRIMP',
        'DIODE SMD', 'DIODE THRU', 'LED SMD', 'BRIDGE RECTIFIER', 'ZENER SMD',
        'RES SMD', 'RES THRU', 'RES ARRAY SMD', 'VARISTOR',
        'CAP CER SMD', 'CAP TANT SMD', 'CAP AL SMD', 'CAP MICA SMD',
        'CAP ELEC THRU', 'TRANSFORMER SMD', 'INDUCTOR SMD', 'RELAY',
        'CRYSTAL AT', 'CRYSTAL OSC', 'CRYSTAL VCXO',
        'CONN MODULAR', 'CONN SECII', 'CONN TERMINAL DMC',
        'LIGHT PIPE',  'MODULE SMPS', 'SWITCH TACT'
    ]

    _url_base = 'http://www.digikey.com'
    _vendorlogo = '/static/images/vendor-logo-digikey.png'
    _search_url_base = urlparse.urljoin(_url_base, '/product-search/en/')
    _default_urlparams = [
        ('stock', '0'), ('mnonly', '0'), ('newproducts', '0'),
        ('ColumnSort', '0'), ('page', '1'), ('quantity', '0'),
        ('ptm', '0'), ('fid', '0'), ('pagesize', '500'),
        ('pbfree', '0'), ('rohs', '0')
    ]

    _type = 'DIGIKEY'

    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code='USD', currency_symbol='US$', **kwargs):
        self._searchpages_filters = {}
        self._session = www.get_session()
        super(VendorDigiKey, self).__init__(
            name, dname, pclass, mappath,
            currency_code, currency_symbol, **kwargs
        )
        self.add_order_baseprice_component("Shipping Cost", 40)
        self.add_order_additional_cost_component("Customs", 12.85)

    @property
    def session(self):
        return self._session

    def get_soup(self, url):
        """
        Retrieve the soup for a particular url. This function is factored out
        to allow switching between the :mod:`urllib2` and :mod:`requests`
        based implementations in :mod:`tendril.utils.www`.

        Currently, the requests based implementation is about two times slower
        for vendor map generation. The cache provided by :mod:`cachecontrol`
        in that implementation is not very well suited to this application.
        Additional changes to the underlying implementation or configuration
        thereof (perhaps in the heuristic) may change this in the future.

        """
        # return www.get_soup_requests(url, session=self._session)
        return www.get_soup(url)

    def search_vpnos(self, ident):
        device, value, footprint = parse_ident(ident)
        if device not in self._devices:
            return None, 'NODEVICE'
        try:
            if device.startswith('RES') or \
                    device.startswith('POT') or \
                    device.startswith('CAP') or \
                    device.startswith('CRYSTAL') or \
                    device.startswith('LED'):
                if check_for_std_val(ident) is False:
                    return self._get_search_vpnos(device, value, footprint)
                try:
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

    rex_to_package = re.compile(ur'^TO(?P<code>[\d]+[A-Za-z]*)$')

    def _search_preprocess(self, device, value, footprint):
        """
        Pre-processes and returns the ``(device, value, footprint)`` tuple
        parsed from the part ident, making tweaks necessary to translate
        the names into those more likely to be found on Digi-Key.

        .. hint::
            This function handles instance-specific tweaks, and should be
            modified to match your instance's nomenclature guidelines.

        .. todo::
            The content of this function should be moved out of the core and
            into the instance folder.

        """
        if footprint is not None:
            m = self.rex_to_package.match(footprint)
            if m:
                footprint = 'TO-' + m.group('code')
        return device, value, footprint

    @staticmethod
    def _process_product_page(soup):
        """
        Given the BS4 parsed soup of a Digi-Key product page, returns a
        :class:`.vendors.SearchResult` instance, whose ``parts`` variable
        includes a list of exactly one :class:`.vendors.SearchPart`
        instance, with relevant data parsed from the page contained
        within it. The ``strategy`` for the returned result is set to
        ``EXACT_MATCH``.

        In case any of the following exclusion criteria are met, the
        part is not returned within the :class:`.vendors.SearchResult`, its
        ``success`` parameter is set to ``False``, and its ``strategy``
        parameter is set as listed below :

        +----------------------------------------+-----------------------+
        | Listed as Obsolete on the Product Page | ``OBSOLETE_NOTAVAIL`` |
        +----------------------------------------+-----------------------+
        | No Part Number Found                   | ``NO_PNO_CELL``       |
        +----------------------------------------+-----------------------+
        | Product Details Table Not Found        | ``NO_PDTABLE``        |
        +----------------------------------------+-----------------------+

        .. todo::
            The current approach of handling catergories and subcategories
            can result in these seemingly 'exact match' results to be put
            into a comparison. If that were to happen, the Package/Case,
            Unit Price, and MOQ are all necessary pieces of information to
            determine inclusion. These are not currently parsed from the
            page soup and should be handled here, preferably without
            instantiating a full digikey part instance.

        """
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
        """
        Given a certain ``device`` string, returns the known Digi-Key
        categories which should be searched in case the first search attempt
        returns an Index Page.

        Returns a ``tuple``, the first element being ``success``
        (``True`` or ``False``) and the second being the list of recognized
        category strings for the given device string.

        .. hint::
            This function handles instance-specific tweaks, and should be
            modified to match your instance's engineering and nomenclature
            guidelines.

        .. todo::
            The content of this function should be moved out of the core and
            into the instance folder.

        """
        if device.startswith('IC'):
            catstrings = ['Integrated Circuits (ICs)',
                          'Isolators',
                          'Sensors, Transducers']
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
        """
        Given a certain ``device`` string, returns the known Digi-Key
        sub-categories which should be searched in case the a search attempt
        returns a Secondary Index Page.

        Returns a ``tuple``, the first element being ``success``
        (``True`` or ``False``) and the second being the list of recognized
        sub-category strings for the given device string.

        .. hint::
            This function handles instance-specific tweaks, and should be
            modified to match your instance's engineering and nomenclature
            guidelines.

        .. todo::
            The content of this function should be moved out of the core and
            into the instance folder.

        """
        if device.startswith('IC'):
            subcatstrings = ['Interface - Controllers']
        elif device.startswith('DIODE'):
            subcatstrings = ['Diodes - Rectifiers - Single',
                             'Diodes - Rectifiers - Arrays']
        elif device.startswith('TRANSISTOR'):
            subcatstrings = ['Transistors - FETs, MOSFETs - Single',
                             'Transistors - FETs, MOSFETs - Arrays']
        elif device.startswith('BRIDGE RECTIFIER'):
            subcatstrings = ['Bridge Rectifiers',
                             'Diodes - Bridge Rectifiers']
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
            new_url = urlparse.urljoin(self._url_base, url_part)
            soup = self.get_soup(new_url)
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
            new_url = urlparse.urljoin(self._url_base, url_part)
            soup = self.get_soup(new_url)
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
        Given a row from a CSV file obtained from Digi-Key's search
        interface and read in using :class:`csv.DictReader`, convert it into
        a :class:`.vendors.SearchPart` instance.

        If the unit price for the row is not readily parseable into a
        float, or if the minqty field includes a Non-Stock note, the
        returned SearchPart has it's ``ns`` attribute set to True.

        :type row: dict
        :rtype: :class:`.vendors.SearchPart`
        """
        pno = row.get('Digi-Key Part Number', '').strip()
        package = row.get('Package / Case', '').strip()
        minqty = row.get('Minimum Quantity', '').strip()
        mfgpno = row.get('Manufacturer Part Number', '').strip()
        unitp = row.get('Unit Price (USD)', '').strip()
        qtyavail = row.get('Quantity Available', '0').strip()
        qtyavail = int(qtyavail)
        try:
            unitp = locale.atof(unitp)
        except ValueError:
            unitp = None
        if pno is not None:
            if qtyavail == 0 or unitp is None:
                ns = True
            else:
                ns = False
        else:
            ns = True
        part = SearchPart(pno=pno, mfgpno=mfgpno, package=package,
                          ns=ns, unitp=unitp, minqty=minqty, raw=row)
        return part

    def _get_resultpage_parts(self, rows):
        """
        Given a list of table rows obtained using a
        :func:`_get_resultpage_table`, or a combined list from multiple
        calls thereof with multiple result pages, returns a
        :class:`.vendors.SearchResult` instance whose ``parts`` variable is a
        list of all Digi-Key parts found in those result pages, each
        represented by a :class:`.vendors.SearchPart` instance and generated
        using :func:`_process_resultpage_row`.
        """
        parts = []
        for row in rows:
            part = self._process_resultpage_row(row)
            parts.append(part)
        return SearchResult(True, parts, '')

    def _get_resultpage_table(self, soup):
        """
        Given the BS4 parsed soup of a Digi-Key search page, returns a
        list of rows in the table.

        This function uses the 'Download table as CSV' feature of Digi-Keys
        website to obtain the table as CSV, and then uses
        :class:`csv.DictReader` to parse the CSV file and returns a list
        of dictionaries - one for each row.

        Each row is intended for later processing into a
        :class:`.vendors.SearchPart` instance using
        :func:`_process_resultpage_row`.

        """
        form = soup.find('form', {'name': 'downloadform'})
        if form is None:
            raise ValueError
        params = []
        parts = form.findAll('input')
        for part in parts:
            params.append((part.attrs['name'], part.attrs['value']))

        target = urlparse.urljoin(self._url_base,
                                  form.attrs['action'])
        url_dl = target + '?' + urllib.urlencode(params)

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
        params = copy(self._default_urlparams)

        searchurl = self._search_url_base + '?k=' + urllib.quote_plus(value) \
            + '&' + urllib.urlencode(params)

        soup = self.get_soup(searchurl)
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

    _regex_fo_res = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[kKMGT])*$')

    def _tf_resistance_to_canonical(self, rstr):
        # TODO Replace with tendril.utils.type version
        rstr = rstr.encode('ascii', 'replace').strip()
        if rstr == '-':
            return
        if rstr == '*':
            return
        if ',' in rstr:
            return
        try:
            rparts = self._regex_fo_res.search(rstr).groupdict()
        except AttributeError:
            raise

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
        vfmt = lambda d: str(d.quantize(Decimal(1))
                             if d == d.to_integral() else d.normalize())
        return vfmt(rval) + ostr

    @staticmethod
    def _tf_tolerance_to_canonical(tstr):
        tstr = www.strencode(tstr).strip()
        return tstr

    _regex_fo_cap = re.compile(r'^(?P<num>\d+(.\d+)*)(?P<order>[pum]F)$')

    def _tf_capacitance_to_canonical(self, cstr):
        # TODO Replace with tendril.utils.type version
        cstr = www.strencode(cstr).strip()
        if cstr == '-':
            return
        if cstr == '*':
            return

        try:
            cparts = self._regex_fo_cap.search(cstr).groupdict()
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

        vfmt = lambda d: str(d.quantize(Decimal(1))
                             if d == d.to_integral() else d.normalize())
        return vfmt(cval) + ostrs[oindex]

    @staticmethod
    def _tf_option_base(ostr):
        ostr = www.strencode(ostr).strip()
        if ostr == '-':
            return
        if ostr == '*':
            return
        return ostr

    @property
    def _filter_otf(self):
        return {
            'Resistance (Ohms)': self._tf_resistance_to_canonical,
            'Capacitance': self._tf_capacitance_to_canonical,
            'Tolerance': self._tf_tolerance_to_canonical,
            'base': self._tf_option_base,
        }

    def _get_searchpage_filters(self, soup):
        filters = {}
        idx = 0
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
                options = [(www.strencode(o.text).rstrip('\n').strip(),
                            o.attrs['value']) for o in optionsoup]
                fname = fvalueselects[idx].attrs['name']
                fname = fname.encode('ascii', 'replace').strip()
                if header in self._filter_otf.keys():
                    options = [
                        (self._filter_otf[header](option[0]), option[1])
                        for option in options
                    ]
                else:
                    options = [
                        (self._filter_otf['base'](option[0]), option[1])
                        for option in options
                    ]
                filters[header] = (fname, options)
        except Exception:
            logger.error(traceback.format_exc())
            logger.error('idx :' + str(idx))
            return False, None
        return True, filters

    def _get_searchurl_filters(self, searchurl):
        if searchurl in self._searchpages_filters.keys():
            return self._searchpages_filters[searchurl]
        else:
            searchsoup = self.get_soup(searchurl)
            result, filters = self._get_searchpage_filters(searchsoup)
            if result is True:
                self._searchpages_filters[searchurl] = filters
            else:
                raise AttributeError
        return filters

    @staticmethod
    def _tf_package_tant_smd(footprint):
        if footprint == 'TANT-B':
            footprint = 'B'
        if footprint == 'TANT-C':
            footprint = 'C'
        if footprint == 'TANT-D':
            footprint = 'D'
        return footprint, None

    @staticmethod
    def _tf_package_crystal_at(footprint):
        extraparams_fp = None
        if footprint == 'HC49':
            footprint = ['HC-49S', 'HC49/U', 'HC49/US']
            extraparams_fp = [('Mounting Type', 'Through Hole'),]
        return footprint, extraparams_fp

    @staticmethod
    def _tf_package_res_array_smd(footprint):
        extraparams_fp = None
        if footprint == '1206-4':
            footprint = '1206'
            extraparams_fp = [('Number of Resistors', '4')]
        return footprint, extraparams_fp

    @property
    def _searchurl_res_smd(self):
        return urlparse.urljoin(self._search_url_base,
                                'resistors/chip-resistor-surface-mount/')

    @property
    def _searchurl_res_thru(self):
        return urlparse.urljoin(self._search_url_base,
                                'resistors/through-hole-resistors/')

    @property
    def _searchurl_res_array_smd(self):
        return urlparse.urljoin(self._search_url_base,
                                'resistors/resistor-networks-arrays/')

    @property
    def _searchurl_cap_cer_smd(self):
        return urlparse.urljoin(self._search_url_base,
                                'capacitors/ceramic-capacitors/')

    @property
    def _searchurl_cap_tant_smd(self):
        return urlparse.urljoin(self._search_url_base,
                                'capacitors/tantalum-capacitors/')

    @property
    def _searchurl_crystal(self):
        return urlparse.urljoin(self._search_url_base,
                                'crystals-oscillators-resonators/crystals/')

    def _get_device_searchparams(self, device):
        packagetf = None
        package_header = 'Package / Case'
        package_filter_type = 'contains'
        extraparams = None
        if device == "RES SMD":
            searchurlbase = self._searchurl_res_smd
            devtype = 'resistor'
        elif device == "RES THRU":
            searchurlbase = self._searchurl_res_thru
            extraparams = (('Tolerance', '+/-1%'),)
            package_filter_type = None
            devtype = 'resistor'
        elif device == "RES POWER":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES ARRAY THRU":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "RES ARRAY SMD":
            searchurlbase = self._searchurl_res_array_smd
            packagetf = self._tf_package_res_array_smd
            devtype = 'resistor_array'
            extraparams = (('Circuit Type', 'Isolated'), )
        elif device == "POT TRIM":
            devtype = 'resistor'
            raise NotImplementedError
        elif device == "CAP CER SMD":
            searchurlbase = self._searchurl_cap_cer_smd
            devtype = 'capacitor'
        elif device == "CAP TANT SMD":
            searchurlbase = self._searchurl_cap_tant_smd
            packagetf = self._tf_package_tant_smd
            package_header = 'Manufacturer Size Code'
            package_filter_type = 'equals'
            devtype = 'capacitor'
        elif device == "CAP CER THRU":
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
            searchurlbase = self._searchurl_crystal
            packagetf = self._tf_package_crystal_at
            package_filter_type = 'inlist'
            extraparams = (('Operating Mode', 'Fundamental'),)
            devtype = 'crystal'
        elif device == "LED SMD":
            raise NotImplementedError
        else:
            raise NotImplementedError
        return (devtype, searchurlbase, packagetf, package_header,
                package_filter_type, extraparams)

    @staticmethod
    def _get_value_options(devtype, value):
        if devtype == 'resistor':
            loptions = (
                ('resistance', "Resistance (Ohms)", 'equals', Resistance),
                ('wattage', "Power (Watts)", 'contains', ThermalDissipation)
            )
            lvalues = parse_resistor(value)
        elif devtype == 'resistor_array':
            loptions = (
                ('resistance', "Resistance (Ohms)", 'equals', Resistance),
                ('wattage', "Power Per Element", 'tequals', ThermalDissipation)
            )
            lvalues = parse_resistor(value)
        elif devtype == 'capacitor':
            loptions = (
                ('capacitance', "Capacitance", 'equals', Capacitance),
                ('voltage', "Voltage - Rated", 'equals', Voltage)
            )
            lvalues = parse_capacitor(value)
        elif devtype == 'crystal':
            loptions = (
                ('frequency', "Frequency", 'equals', Frequency),
            )
            lvalues = [parse_crystal(value)]
        else:
            raise ValueError
        return loptions, lvalues

    @staticmethod
    def _process_value_options(filters, loptions, lvalues):
        lparams = []

        for lidx, loption in enumerate(loptions):
            if lvalues[lidx] is None:
                continue
            dkopcode = None

            for option in filters[loption[1]][1]:
                if loption[2] == 'equals':
                    if option[0] == lvalues[lidx]:
                        dkopcode = option[1]
                elif loption[2] == 'contains':
                    if option[0] and lvalues[lidx] in option[0]:
                        dkopcode = option[1]
                elif loption[2] == 'tequals':
                    t = loption[3]
                    if not option[0]:
                        continue
                    if ',' in option[0]:
                        val = option[0].split(',')[0]
                    else:
                        val = option[0]
                    if t(val) == t(lvalues[lidx]):
                        dkopcode = option[1]

            dkfiltcode = filters[loption[1]][0]
            if dkopcode is None:
                raise ValueError(loption[0] + ' ' + lvalues[lidx])
            lparams.append((dkfiltcode, dkopcode))

        return lparams

    @staticmethod
    def _process_package_options(filters, package_header,
                                 package_filter_type, footprint):
        if package_filter_type is not None:
            lparams = []
            pkgopcode = None
            for option in filters[package_header][1]:
                if not option[0]:
                    continue
                if package_filter_type == 'contains':
                    if footprint in option[0]:
                        try:
                            pkgopcode.append(option[1])
                        except AttributeError:
                            pkgopcode = [option[1]]
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
                    lparams.append((filters[package_header][0], opt))
            else:
                lparams.append((filters[package_header][0], pkgopcode))
            return lparams
        else:
            return []

    @staticmethod
    def _process_extraparams(filters, extraparams):
        lparams = []
        if extraparams is not None:
            for param in extraparams:
                opcode = None
                for option in filters[param[0]][1]:
                    if option[0] == param[1]:
                        opcode = option[1]
                if opcode is None:
                    raise ValueError("Param not valid: " + str(param))
                lparams.append((filters[param[0]][0], opcode))
        return lparams

    def _get_pas_vpnos(self, device, value, footprint):
        devtype, searchurlbase, packagetf, package_header, \
            package_filter_type, extraparams = \
            self._get_device_searchparams(device)
        filters = self._get_searchurl_filters(searchurlbase)
        params = copy(self._default_urlparams)
        loptions, lvalues = self._get_value_options(devtype, value)

        params.extend(
            self._process_value_options(filters, loptions, lvalues)
        )

        extraparams_fp = None
        if packagetf is not None:
            footprint, extraparams_fp = packagetf(footprint)

        packages_handled = False
        package_params = self._process_package_options(
            filters, package_header, package_filter_type, footprint
        )
        if len(package_params):
            packages_handled = True
            params.extend(package_params)

        if extraparams_fp is not None:
            if extraparams is not None:
                extraparams = list(extraparams) + extraparams_fp
            else:
                extraparams = extraparams_fp
        params.extend(self._process_extraparams(filters, extraparams))
        searchurl = searchurlbase + '?' + urllib.urlencode(params)
        soup = self.get_soup(searchurl)
        if soup is None:
            return None, 'URL_FAIL'

        ptable = soup.find('table', id='productTable')
        if ptable is None:
            # check for single product page
            sr = self._process_product_page(soup)
            if sr.success is True:
                # Sent directly to an exact match. Just send it back.
                return [sr.parts[0]['Digi-Key Part Number']], sr.strategy

        try:
            table = self._get_resultpage_table(soup)
        except ValueError:
            return None, 'NO_RESULTS:PAS1'
        sr = self._get_resultpage_parts(table)
        if sr.success is False:
            return SearchResult(False, None, sr.strategy)
        if sr.parts is None:
            raise Exception
        if len(sr.parts) == 0:
            return None, 'NO_RESULTS:PAS2'

        results = sr.parts
        if not packages_handled:
            sr = self._process_results(results, value, footprint)
        else:
            sr = self._filter_results_unfiltered(results)
        if sr.success is False:
            return None, sr.strategy
        return sr.parts, sr.strategy


dvobj = VendorDigiKey('digikey', 'Digi-Key Corporation',
                      'electronics', mappath=None,
                      currency_code='USD', currency_symbol='US$')
