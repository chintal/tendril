"""
Vendors module documentation (:mod:`sourcing.vendors`)
======================================================
"""

import utils.log
logger = utils.log.get_logger(__name__, utils.log.INFO)

import os
import csv
import time

import entityhub.maps
import utils.currency
import utils.config


class VendorOrder(object):
    def __init__(self, vendor, orderref):
        self._vendor = vendor
        self._lines = []
        self._basecost = self._vendor.order_baseprice
        self._orderref = orderref

    def add(self, line):
        self._lines.append(line)

    def __len__(self):
        return len(self._lines)

    @property
    def lines(self):
        return self._lines

    @property
    def orderref(self):
        return self._orderref


class VendorBase(object):
    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=utils.config.BASE_CURRENCY,
                 currency_symbol=utils.config.BASE_CURRENCY_SYMBOL):
        self._name = name
        self._mappath = None
        self._map = None
        self._dname = dname
        self._currency = utils.currency.CurrencyDefinition(currency_code, currency_symbol)
        self._pclass = pclass
        self._order = None
        self._orderbasecosts = []
        self._orderadditionalcosts = []
        if mappath is not None:
            self.map = mappath

    @property
    def name(self):
        return self._dname

    @property
    def pclass(self):
        return self._pclass

    @property
    def mappath(self):
        return self._mappath

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, mappath):
        self._mappath = mappath
        if os.path.isfile(mappath) is False:
            if 'electronics' in self._pclass:
                import electronics
                electronics.gen_vendor_mapfile(self)
            else:
                raise AttributeError
        self._map = entityhub.maps.MapFile(mappath)

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, currency_def):
        """

        :type currency_def: utils.currency.CurrencyDefinition
        """
        self._currency = currency_def

    def get_vpnos(self, ident):
        return self._map.get_partnos(ident)

    def search_vpnos(self, ident):
        raise NotImplementedError

    def get_vpart(self, vpartno, ident=None):
        raise NotImplementedError

    def get_optimal_pricing(self, ident, rqty):
        candidate_names = self.get_vpnos(ident)

        candidates = [self.get_vpart(x) for x in candidate_names]

        candidates = [x for x in candidates if x.abs_moq <= rqty]
        candidates = [x for x in candidates if x.vqtyavail is None or x.vqtyavail > rqty or x.vqtyavail == -2]

        oqty = rqty

        # vobj, vpno, oqty, nbprice, ubprice, effprice
        if len(candidates) == 0:
            return self, None, None, None, None, None

        selcandidate = candidates[0]
        tcost = self.get_effective_price(selcandidate.get_price(rqty)[0]).extended_price(rqty).native_value

        for candidate in candidates:
            ubprice, nbprice = candidate.get_price(oqty)
            effprice = self.get_effective_price(ubprice)
            ntcost = effprice.extended_price(oqty).native_value
            if ntcost < tcost:
                tcost = ntcost
                selcandidate = candidate

        if selcandidate.vqtyavail == -2:
            logger.warning("Vendor available quantity could not be confirmed. Verify manually : "
                           + self.name + " " + selcandidate.vpno + os.linesep + os.linesep + os.linesep )

        ubprice, nbprice = selcandidate.get_price(oqty)
        effprice = self.get_effective_price(ubprice)
        urationale = None
        olduprice = None
        if nbprice is not None:
            nubprice, nnbprice = selcandidate.get_price(nbprice.moq)
            neffprice = self.get_effective_price(nubprice)
            ntcost = neffprice.extended_price(nbprice.moq).native_value

            bump_excess_qty = nubprice.moq - rqty

            if ntcost < tcost * 1.4:
                urationale = "TC Increase < 40%"
                oqty = nbprice.moq
                olduprice = ubprice
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice
            elif nubprice.unit_price.native_value < ubprice.unit_price.native_value * 0.5:
                urationale = "UP Decrease > 40%"
                olduprice = ubprice
                oqty = nbprice.moq
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice
        return self, selcandidate.vpno, oqty, nbprice, ubprice, effprice, urationale, olduprice

    def add_order_additional_cost_component(self, desc, percent):
        self._orderadditionalcosts.append((desc, percent))

    def get_effective_price(self, price):
        effective_unitp = price.unit_price.source_value
        for additional_cost in self._orderadditionalcosts:
            effective_unitp += price.unit_price.source_value * float(additional_cost[1]) / 100
        return VendorPrice(price.moq, effective_unitp, self.currency, price.oqmultiple)

    def get_additional_costs(self, price):
        rval = []
        for desc, percent in self._orderadditionalcosts:
            rval.append((desc, price.source_value * percent / 100))
        return rval

    @property
    def order_baseprice(self):
        t = 0
        for price in self._orderbasecosts:
            t += price[1].native_value
        return utils.currency.CurrencyValue(t, utils.currency.native_currency_defn)

    def add_order_baseprice_component(self, desc, value):
        if isinstance(value, utils.currency.CurrencyValue):
            self._orderbasecosts.append((desc, value))
        else:
            self._orderbasecosts.append((desc, utils.currency.CurrencyValue(value, self.currency)))

    def add_to_order(self, line, orderref=None):
        if self._order is None:
            self._order = VendorOrder(self, orderref)
        logger.info("Adding to " + self._name + " order : " + line[0] + " : " + str(line[3]))
        self._order.add(line)

    def _dump_open_order(self, path):
        orderfile = os.path.join(path, self._name + '-order.csv')
        with open(orderfile, 'w') as orderf:
            w = csv.writer(orderf)
            w.writerow([self._dname + " Order", None, None, None, None, time.strftime("%c")])
            w.writerow(["Ident", "Vendor Part No", "Quantity",
                        "Unit Price (" + self._currency.symbol + ")",
                        "Extended Price (" + self._currency.symbol + ")",
                        "Effective Price (" + utils.currency.native_currency_defn.symbol + ")"
                        ])
            for line in self._order.lines:
                w.writerow([line[0], line[2], line[3],
                            line[5].unit_price.source_value,
                            line[5].extended_price(line[3]).source_value,
                            line[6].extended_price(line[3]).native_value])
            for basecost in self._orderbasecosts:
                w.writerow([None, basecost[0], None, None, basecost[1].source_value, basecost[1].native_value])

    def _generate_purchase_order(self, path):
        stagebase = {}
        return stagebase

    def finalize_order(self, path):
        if self._order is None or len(self._order) == 0:
            logger.debug("Nothing in the order, not generating order file : " + self._name)
            return
        logger.info("Writing " + self._dname + " order to Folder : " + path)
        self._dump_open_order(path)
        self._generate_purchase_order(path)
        self._order = None


class VendorPrice(object):
    def __init__(self, moq, price, currency_def, oqmultiple=1):
        self._moq = moq
        self._price = utils.currency.CurrencyValue(price, currency_def)
        self._oqmulitple = oqmultiple

    @property
    def moq(self):
        return self._moq

    @property
    def oqmultiple(self):
        return self._oqmulitple

    @property
    def unit_price(self):
        return self._price

    def extended_price(self, qty):
        if qty < self.moq:
            raise ValueError
        if qty % self.oqmultiple != 0:
            pass
        return utils.currency.CurrencyValue(self.unit_price._val * qty,
                                            self.unit_price._currency_def)


class VendorPartBase(object):
    def __init__(self, ident, vendor):
        self._vpno = None
        self._vqtyavail = None
        self._manufacturer = None
        self._mpartno = None
        self._vpartdesc = None
        self._canonical_repr = ident
        self._prices = []
        self._vendor = vendor
        self._pkgqty = 1

    def add_price(self, price):
        self._prices.append(price)

    @property
    def vpno(self):
        return self._vpno

    @vpno.setter
    def vpno(self, value):
        self._vpno = value

    @property
    def vqtyavail(self):
        return self._vqtyavail

    @vqtyavail.setter
    def vqtyavail(self, value):
        self._vqtyavail = value

    @property
    def manufacturer(self):
        return self._manufacturer

    @manufacturer.setter
    def manufacturer(self, value):
        self._manufacturer = value

    @property
    def mpartno(self):
        return self._mpartno

    @mpartno.setter
    def mpartno(self, value):
        self._mpartno = value

    @property
    def vpartdesc(self):
        return self._vpartdesc

    @vpartdesc.setter
    def vpartdesc(self, value):
        self._vpartdesc = value

    @property
    def ident(self):
        return self._canonical_repr

    @property
    def pkgqty(self):
        return self._pkgqty

    @pkgqty.setter
    def pkgqty(self, value):
        self._pkgqty = value

    @property
    def abs_moq(self):
        if len(self._prices) == 0:
            return 0
        rval = self._prices[0].moq
        for price in self._prices:
            if price.moq < rval:
                rval = price.moq
        return rval

    def get_price(self, qty):
        rprice = None
        rnextprice = None
        for price in self._prices:
            if price.moq <= qty:
                if rprice is not None:
                    if price.moq > rprice.moq:
                        rprice = price
                else:
                    rprice = price
            if price.moq > qty:
                if rnextprice is not None:
                    if price.moq < rnextprice.moq:
                        rnextprice = price
                else:
                    rnextprice = price
        return rprice, rnextprice

    def __repr__(self):
        return self.vpno + ' ' + str(self._vpartdesc) + ' ' + str(self.abs_moq) + '\n'


class VendorElnPartBase(VendorPartBase):
    def __init__(self, ident, vendor):
        super(VendorElnPartBase, self).__init__(ident, vendor)
        self._package = None
        self._datasheet = None

    @property
    def package(self):
        return self._package

    @package.setter
    def package(self, value):
        self._package = value

    @property
    def datasheet(self):
        return self._datasheet

    @datasheet.setter
    def datasheet(self, value):
        self._datasheet = value

