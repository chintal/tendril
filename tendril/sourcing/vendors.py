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
Vendors module documentation (:mod:`tendril.sourcing.vendors`)
==============================================================
"""

import os
import csv
import time
from collections import namedtuple
from sqlalchemy.orm.exc import NoResultFound
from six.moves.urllib.error import HTTPError, URLError

from tendril.entityhub.maps import MapFileBase
from tendril.utils.types import currency
from tendril.utils import config
from tendril.utils.db import get_session

from db import controller

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


#: A :class:`collections.namedtuple` used internally to pass
#: around (sub)search results conveniently.
SearchResult = namedtuple('SearchResult', 'success parts strategy')

#: A :class:`collections.namedtuple` used internally to pass
#: around part data conveniently.
SearchPart = namedtuple('SearchPart',
                        'pno, mfgpno, package, ns, unitp,  minqty')

#: A :class:`collections.namedtuple` used internally to pass
#: around sourcing information for a single ident from a single
#: vendor at a specified quantity.
SourcingInfo = namedtuple(
    'SourcingInfo',
    'vobj, vpart, oqty, nbprice, ubprice, effprice, urationale, olduprice'
)


class DBPartDataUnusable(Exception):
    pass


class DBPartDataExpired(DBPartDataUnusable):
    pass


class DBPartDataIncomplete(DBPartDataUnusable):
    pass


class DBPartDataUnavailable(DBPartDataUnusable):
    pass


class VendorMapFileDB(MapFileBase):
    def __init__(self, vendor):
        self._vendor = vendor
        self._vendor_name = vendor._name
        super(VendorMapFileDB, self).__init__(self._vendor.mappath)

    def length(self):
        return controller.get_vendor_map_length(vendor=self._vendor_name)

    def get_user_map(self):
        raise NotImplementedError

    def get_idents(self):
        return [x.ident for x in
                controller.get_vendor_idents(vendor=self._vendor_name)]

    def get_map_time(self, canonical):
        return controller.get_time(vendor=self._vendor_name, ident=canonical)

    def get_canonical(self, partno):
        return controller.get_ident(vendor=self._vendor_name, vpno=partno)

    def get_apartnos(self, canonical):
        return controller.get_amap_vpnos(vendor=self._vendor_name,
                                         ident=canonical)

    def get_upartnos(self, canonical):
        return controller.get_umap_vpnos(vendor=self._vendor_name,
                                         ident=canonical)

    def get_strategy(self, canonical):
        return controller.get_strategy(vendor=self._vendor_name,
                                       ident=canonical)


class VendorInvoiceLine(object):
    def __init__(self, invoice, ident, vpno, unitp, qty, desc=None):
        self._invoice = invoice
        self._ident = ident
        self._vpno = vpno
        self._unitp = unitp
        self._qty = qty
        self._desc = desc

    @property
    def desc(self):
        return self._desc

    @property
    def ident(self):
        return self._ident

    @property
    def vpno(self):
        return self._vpno

    @property
    def unitprice(self):
        return self._unitp

    @property
    def extendedprice(self):
        return currency.CurrencyValue(self._unitp._val * self._qty,
                                      self._unitp._currency_def)

    @property
    def effectiveprice(self):
        return self.extendedprice

    @property
    def qty(self):
        return self._qty


class VendorInvoice(object):
    def __init__(self, vendor, inv_no, inv_date):
        self._vendor = vendor
        self._inv_no = inv_no
        self._inv_date = inv_date
        self._lines = []
        if self._linetype is None:
            self._linetype = VendorInvoiceLine
        self._acquire_lines()

    @property
    def vendor_name(self):
        return self._vendor.name

    @property
    def currency(self):
        return self._vendor.currency

    @property
    def inv_no(self):
        return self._inv_no

    @property
    def inv_date(self):
        return self._inv_date

    @property
    def linecount(self):
        return len(self._lines)

    @property
    def lines(self):
        return self._lines

    @property
    def extendedtotal(self):
        return sum([x.extendedprice for x in self._lines])

    @property
    def effectivetotal(self):
        return sum([x.effectiveprice for x in self._lines])

    def _acquire_lines(self):
        raise NotImplementedError


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


class VendorPrice(object):
    def __init__(self, moq, price, currency_def, oqmultiple=1):
        self._moq = moq
        self._price = currency.CurrencyValue(price, currency_def)
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
        return currency.CurrencyValue(self.unit_price._val * qty,
                                      self.unit_price._currency_def)

    def __repr__(self):
        return '<VendorPrice {2} @{0}({1})>'.format(
            self.moq, self.oqmultiple, self.unit_price)


class VendorPartBase(object):
    def __init__(self, vpno, ident, vendor, max_age=600000):
        self._vpno = vpno
        self._vqtyavail = None
        self._manufacturer = None
        self._mpartno = None
        self._vpartdesc = None
        self._canonical_repr = ident
        self._prices = []
        self._vendor = vendor
        self._pkgqty = 1
        self._last_updated = None
        self._populate(max_age)

    def _populate(self, max_age):
        if self._vendor is not None and self._canonical_repr is not None:
            with get_session() as s:
                if max_age > 0:
                    try:
                        self.load_from_db(max_age, s)
                        return
                    except DBPartDataUnusable:
                        pass
                self._get_data()
                try:
                    self.commit(s)
                except NoResultFound:
                    pass
        else:
            self._get_data()

    def commit(self, session=None):
        if session is None:
            with get_session() as s:
                self._commit_to_db(session=s)
        else:
            self._commit_to_db(session=session)

    def _commit_to_db(self, session):
        vpno = controller.get_vpno_obj(
            vendor=self._vendor._name, ident=self._canonical_repr,
            vpno=self._vpno, session=session
        )
        controller.populate_vpart_detail(
            vpno=vpno, vpart=self, session=session
        )
        controller.populate_vpart_prices(
            vpno=vpno, vpart=self, session=session
        )
        return vpno

    def load_from_db(self, max_age, session=None):
        if session is None:
            with get_session() as s:
                self._load_from_db(max_age, session=s)
        else:
            self._load_from_db(max_age, session=session)

    def _load_from_db(self, max_age, session):
        try:
            vpno = controller.get_vpno_obj(
                vendor=self._vendor._name, ident=self._canonical_repr,
                vpno=self._vpno, session=session
            )
            data_ts = vpno.updated_at.timestamp
            now = time.time()
            if now - data_ts > max_age:
                raise DBPartDataExpired
            self._vqtyavail = vpno.detail.vqtyavail
            self._manufacturer = vpno.detail.manufacturer
            self._mpartno = vpno.detail.mpartno
            self._vpartdesc = vpno.detail.vpartdesc
            self._pkgqty = vpno.detail.pkgqty
            self._last_updated = vpno.updated_at
            for price in vpno.prices:
                self.add_price(
                    VendorPrice(int(price.moq), float(price.price),
                                self._vendor.currency, int(price.oqmultiple))
                )
            return vpno
        except NoResultFound:
            raise DBPartDataUnavailable
        except AttributeError:
            raise DBPartDataIncomplete

    def _get_data(self):
        raise NotImplementedError

    def add_price(self, price):
        self._prices.append(price)

    @property
    def last_updated(self):
        return self._last_updated

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
        if self._manufacturer is not None:
            return self._manufacturer
        elif self._vendor.is_manufacturer:
            return self._vendor.name

    @manufacturer.setter
    def manufacturer(self, value):
        self._manufacturer = value

    @property
    def mpartno(self):
        if self._mpartno is not None:
            return self._mpartno
        elif self._vendor.is_manufacturer:
            return self._vpno

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

    @property
    def vpart_url(self):
        return None

    @property
    def prices(self):
        return sorted(self._prices, key=lambda x: x.moq)

    @property
    def effective_prices(self):
        return [self._vendor.get_effective_price(x) for x in self.prices]

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
        return '<{0} {1} {2}>'.format(
            self.__class__, self.vpno,  str(self._vpartdesc)
        )


class VendorElnPartBase(VendorPartBase):
    def __init__(self, vpno, ident, vendor, max_age):
        self._package = None
        self._datasheet = None
        super(VendorElnPartBase, self).__init__(vpno, ident, vendor, max_age)

    def _commit_to_db(self, session):
        vpno = super(VendorElnPartBase, self)._commit_to_db(session=session)
        controller.populate_vpart_detail_eln(
            vpno=vpno, vpart=self, session=session
        )
        return vpno

    def _load_from_db(self, max_age, session):
        vpno = super(VendorElnPartBase, self)._load_from_db(max_age,
                                                            session=session)
        if vpno is not None:
            self._package = vpno.detail_eln.package
            self._datasheet = vpno.detail_eln.datasheet

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


class VendorBase(object):
    _vendorlogo = None
    _partclass = VendorPartBase
    _invoiceclass = VendorInvoice
    _type = 'BASE'
    _url_base = None

    def __init__(self, name, dname, pclass, mappath=None,
                 currency_code=config.BASE_CURRENCY,
                 currency_symbol=config.BASE_CURRENCY_SYMBOL,
                 vendorlogo=None, sname=None, is_manufacturer=None):
        self._name = name
        self._dname = dname
        self._sname = sname
        self._instance_vendorlogo = vendorlogo
        self._is_manufacturer = is_manufacturer
        self._currency = currency.CurrencyDefinition(currency_code,
                                                     currency_symbol)
        self._pclass = pclass
        self._order = None
        self._orderbasecosts = []
        self._orderadditionalcosts = []
        if mappath is not None:
            self._mappath = mappath
        else:
            self._mappath = self._name + '-' + self._pclass + '.csv'
        self._map = VendorMapFileDB(self)

    @property
    def name(self):
        if self._dname is not None:
            return self._dname
        else:
            return self._name

    @property
    def sname(self):
        if self._sname is not None:
            return self._sname
        else:
            return self._name

    @property
    def pclass(self):
        return self._pclass

    @property
    def type(self):
        return self._type

    @property
    def is_manufacturer(self):
        if self._is_manufacturer is None:
            return False
        return self._is_manufacturer

    @property
    def mappath(self):
        return self._mappath

    @property
    def map(self):
        return self._map

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, currency_def):
        """

        :type currency_def: utils.currency.CurrencyDefinition
        """
        self._currency = currency_def

    @property
    def logo(self):
        if self._instance_vendorlogo is not None:
            return self._instance_vendorlogo
        return self._vendorlogo

    @property
    def url_base(self):
        try:
            return self._url_base
        except AttributeError:
            return None

    def get_idents(self):
        for ident in self._map.get_idents():
            yield ident

    def get_all_vpnos(self):
        for ident in self.get_idents():
            for vpno in self._map.get_all_partnos(ident):
                yield ident, vpno

    def get_all_vparts(self, max_age=600000):
        for ident, vpno in self.get_all_vpnos():
            yield self.get_vpart(vpartno=vpno, ident=ident, max_age=max_age)

    def get_vpnos(self, ident, max_age=600000):
        mtime = self._map.get_map_time(canonical=ident)
        now = time.time()
        if not mtime or now - mtime > max_age:
            try:
                vpnos, strategy = self.search_vpnos(ident)
                with get_session() as session:
                    controller.set_strategy(vendor=self._name, ident=ident,
                                            strategy=strategy, session=session)
                    controller.set_amap_vpnos(vendor=self._name, ident=ident,
                                              vpnos=vpnos, session=session)
            except (NotImplementedError, URLError, HTTPError):
                pass
        return self._map.get_partnos(ident)

    def search_vpnos(self, ident):
        raise NotImplementedError

    def get_vpart(self, vpartno, ident=None, max_age=600000):
        return self._partclass(vpartno, ident, self, max_age)

    def _get_candidate_tcost(self, candidate, oqty):
        ubprice, nbprice = candidate.get_price(oqty)
        effprice = self.get_effective_price(ubprice)
        return effprice.extended_price(oqty).native_value

    def _get_candidate_isinfo(self, candidate, oqty):
        tcost = self._get_candidate_tcost(candidate, oqty)
        ubprice, nbprice = candidate.get_price(oqty)
        effprice = self.get_effective_price(ubprice)
        urationale = None
        olduprice = None
        if nbprice is not None:
            nubprice, nnbprice = candidate.get_price(nbprice.moq)
            neffprice = self.get_effective_price(nubprice)
            ntcost = neffprice.extended_price(nbprice.moq).native_value
            # bump_excess_qty = nubprice.moq - rqty

            if ntcost < tcost * 1.4:
                urationale = "TC Increase < 40%"
                oqty = nbprice.moq
                olduprice = ubprice
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice
            elif nubprice.unit_price.native_value < \
                    ubprice.unit_price.native_value * 0.5:
                urationale = "UP Decrease > 40%"
                olduprice = ubprice
                oqty = nbprice.moq
                ubprice = nubprice
                nbprice = nnbprice
                effprice = neffprice
        return SourcingInfo(self, candidate, oqty, nbprice,
                            ubprice, effprice, urationale, olduprice)

    def get_optimal_pricing(self, ident, rqty, get_all=False):
        candidate_names = self.get_vpnos(ident)

        candidates = [self.get_vpart(x, ident=ident) for x in candidate_names]
        candidates = [x for x in candidates if x.abs_moq <= rqty]
        candidates = [x for x in candidates
                      if x.vqtyavail is None or
                      x.vqtyavail > rqty or
                      x.vqtyavail == -2]
        oqty = rqty

        if len(candidates) == 0:
            if not get_all:
                return SourcingInfo(self, None, None, None,
                                    None, None, None, None)
            else:
                return []

        if get_all:
            return [self._get_candidate_isinfo(x, oqty) for x in candidates]

        selcandidate = candidates[0]
        tcost = self.get_effective_price(
            selcandidate.get_price(rqty)[0]
        ).extended_price(rqty).native_value

        for candidate in candidates:
            ntcost = self._get_candidate_tcost(candidate, oqty)
            if ntcost < tcost:
                tcost = ntcost
                selcandidate = candidate

        if selcandidate.vqtyavail == -2:
            logger.warning(
                "Vendor available quantity could not be confirmed. "
                "Verify manually : " + self.name + " " + selcandidate.vpno +
                os.linesep + os.linesep + os.linesep
            )

        return self._get_candidate_isinfo(selcandidate, oqty)

    def add_order_additional_cost_component(self, desc, percent):
        self._orderadditionalcosts.append((desc, percent))

    def get_effective_price(self, price):
        # TODO This needs to move into the VendorPart instead
        effective_unitp = price.unit_price.source_value
        for additional_cost in self._orderadditionalcosts:
            effective_unitp += price.unit_price.source_value * float(additional_cost[1]) / 100  # noqa
        return VendorPrice(
            price.moq, effective_unitp, self.currency, price.oqmultiple
        )

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
        return currency.CurrencyValue(t, currency.native_currency_defn)

    def add_order_baseprice_component(self, desc, value):
        if isinstance(value, currency.CurrencyValue):
            self._orderbasecosts.append((desc, value))
        else:
            self._orderbasecosts.append(
                (desc, currency.CurrencyValue(value, self.currency))
            )

    def add_to_order(self, line, orderref=None):
        if self._order is None:
            self._order = VendorOrder(self, orderref)
        logger.info("Adding to " + self._name + " order : " +
                    line[0] + " : " + str(line[3])
                    )
        self._order.add(line)

    def _dump_open_order(self, path):
        orderfile = os.path.join(path, self._name + '-order.csv')
        with open(orderfile, 'w') as orderf:
            w = csv.writer(orderf)
            w.writerow(
                [self._dname + " Order", None, None,
                 None, None, time.strftime("%c")]
            )
            w.writerow(
                ["Ident", "Vendor Part No", "Quantity",
                 "Unit Price (" + self._currency.symbol + ")",
                 "Extended Price (" + self._currency.symbol + ")",
                 "Effective Price (" + currency.native_currency_defn.symbol +
                 ")"
                 ]
            )
            for line in self._order.lines:
                w.writerow([line[0], line[2], line[3],
                            line[5].unit_price.source_value,
                            line[5].extended_price(line[3]).source_value,
                            line[6].extended_price(line[3]).native_value])
            for basecost in self._orderbasecosts:
                w.writerow(
                    [None, basecost[0], None, None, basecost[1].source_value,
                     basecost[1].native_value]
                )

    def _generate_purchase_order(self, path):
        stagebase = {}
        return stagebase

    def finalize_order(self, path):
        if self._order is None or len(self._order) == 0:
            logger.debug("Nothing in the order, "
                         "not generating order file : " + self._name)
            return
        logger.info("Writing " + self._dname + " order to Folder : " + path)
        self._dump_open_order(path)
        self._generate_purchase_order(path)
        self._order = None
