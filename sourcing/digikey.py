"""
Digi-Key Sourcing Module documentation (:mod:`sourcing.digikey`)
================================================================
"""

import vendors
import logging

import utils.wwwutils
import utils.currency

from bs4 import BeautifulSoup
import locale
import re


locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
usd_definition = utils.currency.CurrencyDefinition('USD', 'US$')


class VendorDigiKey(vendors.Vendor):
    def __init__(self, name, dname, mapfile, pclass):
        super(VendorDigiKey, self).__init__(name, dname, mapfile, pclass)


class DigiKeyPart(vendors.VendorElnPart):
    def __init__(self, dkpartno=None):
        super(DigiKeyPart, self).__init__()
        if dkpartno is not None:
            self._dkpartno = dkpartno
        else:
            logging.error("Not enough information to create a Digikey Part")
        self._get_data()

    def _get_data(self):
        url = ('http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail?name='
               + self._dkpartno)
        page = utils.wwwutils.opener.open(url)
        soup = BeautifulSoup(page)

        self._prices = self._get_prices(soup)
        self._mpartno = self._get_mpartno(soup)
        self._manufacturer = self._get_manufacturer(soup)
        self._package = self._get_package(soup)
        self._datasheet = self._get_datasheet_link(soup)

    @staticmethod
    def _get_prices(soup):
        pricingtable = soup.find('table', id='pricing')
        prices = []
        for row in pricingtable.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == 3:
                cells = [cell.text.strip() for cell in cells]
                moq = locale.atoi(cells[0])
                price = locale.atof(cells[1])
                prices.append(vendors.VendorPrice(moq,
                                                  price,
                                                  usd_definition))
        return prices

    @staticmethod
    def _get_mpartno(soup):
        mpart = soup.find('h1', attrs={'class': "seohtag",
                                       'itemprop': "model"})
        return mpart.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_manufacturer(soup):
        mfrer = soup.find('h2', attrs={'class': "seohtag",
                                       'itemprop': "manufacturer"})
        return mfrer.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_package(soup):
        n = soup.findAll('th', text=re.compile('Supplier Device Package'))
        package_cell = n[0].find_next_sibling()
        return package_cell.text.strip().encode('ascii', 'replace')

    @staticmethod
    def _get_datasheet_link(soup):
        n = soup.findAll('th', text=re.compile('Datasheets'))
        datasheet_cell = n[0].find_next_sibling()
        datasheet_link = datasheet_cell.find_all('a')[0].attrs['href']
        return datasheet_link.strip().encode('ascii', 'replace')

    def get_price(self, qty):
        rprice = None
        rnextprice = None
        for price in self._prices:
            if price.moq < qty:
                rprice = price
            if price.moq > qty:
                rnextprice = price
            break
        return [rprice, rnextprice]


def get_dk_part(ident):
    pass
    # Check Maps for predefined
    # Search for part

