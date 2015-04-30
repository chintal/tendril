"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.DEFAULT)

import os
import yaml

import vendors
import utils.currency

from utils.config import PRICELISTVENDORS_FOLDER


class VendorPricelist(vendors.VendorBase):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=None, currency_symbol=None, pricelistpath=None):
        if pricelistpath is None:
            pricelistpath = os.path.join(PRICELISTVENDORS_FOLDER, name + '-pricelist.yaml')
        with open(pricelistpath, 'r') as f:
            self._pricelist = yaml.load(f)
        if currency_code is None:
            currency_code = self._pricelist["currency"]["code"].strip()
        if currency_symbol is None:
            currency_symbol = self._pricelist["currency"]["symbol"].strip()
        self._currency = utils.currency.CurrencyDefinition(currency_code, currency_symbol)
        super(VendorPricelist, self).__init__(name, dname, pclass, mappath,
                                              currency_code, currency_symbol)

    def search_vpnos(self, ident):
        vplist = []
        for part in self._pricelist['prices']:
            if part['ident'] == ident:
                vplist.append(part['vpno'].strip())
        if len(vplist) > 0:
            return vplist, 'MANUAL'
        else:
            return vplist, 'UNDEF'

    def get_vpart(self, vpartno, ident=None):
        vp_dict = self._pl_get_vpart_dict(vpartno)
        if ident is not None:
            if vp_dict['ident'].strip() != ident:
                logger.warning('Specified Ident does not match Pricelist Defined Ident : '
                               + vp_dict['ident'].strip())
        return PricelistPart(vp_dict, ident, self)

    def _pl_get_vpart_dict(self, vpartno):
        for part in self._pricelist["prices"]:
            if part['vpno'].strip() == vpartno:
                return part

    def get_optimal_pricing(self, ident, rqty):
        candidate_names = self.get_vpnos(ident)

        candidates = [self.get_vpart(x) for x in candidate_names]
        if len(candidates) == 0:
            return self, None, None, None, None, None, None, None

        selcandidate = candidates[0]
        tcost, oqty, price = selcandidate.get_price_qty(rqty)
        if len(candidates) > 1:
            for candidate in candidates:
                ltcost, loqty, lprice = candidate.get_price_qty(rqty)
                if ltcost < tcost:
                    tcost = ltcost
                    selcandidate = candidate
                    oqty = loqty
                    price = lprice
        effprice = self.get_effective_price(price)
        return self, selcandidate.vpno, oqty, None, price, effprice, "Vendor MOQ/GL", None


class PricelistPart(vendors.VendorPartBase):
    def __init__(self, vp_dict, ident, vendor):
        self._vendor = vendor
        super(PricelistPart, self).__init__(ident, vendor)
        self.vpno = vp_dict['vpno'].strip()
        if 'pkgqty' in vp_dict.keys():
            self.pkgqty = vp_dict['pkgqty']
        self._vqtyavail = None
        price = vendors.VendorPrice(vp_dict['moq'], vp_dict['unitp'], self._vendor.currency,
                                    vp_dict['oqmultiple'])
        self._prices.append(price)

    def get_price_qty(self, qty):
        lcost = None
        lprice = None
        loqty = None
        for price in self._prices:
            tqty = 0
            while tqty < qty or tqty < price.moq:
                tqty += price.oqmultiple
            tcost = price.extended_price(tqty).native_value
            if lcost is None or tcost < lcost:
                lcost = tcost
                lprice = price
                loqty = tqty
        return lcost, loqty, lprice
