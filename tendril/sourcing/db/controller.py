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
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import arrow

from sqlalchemy.sql import exists
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.exc import NoResultFound

from tendril.utils.db import with_db
from tendril.utils.db import get_session

from model import SourcingVendor
from model import VendorPartMap
from model import VendorPartNumber
from model import VendorPartDetail
from model import VendorElnPartDetail
from model import VendorPrice

from tendril.utils.config import VENDORS_DATA

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


# Argument Processors
@with_db
def _get_vendor(vendor=None, session=None):
    if not vendor:
        raise AttributeError("vendor needs to be defined")
    if isinstance(vendor, str):
        vendor = get_vendor(name=vendor, session=session)
        if not vendor:
            raise ValueError("Could not find vendor {0}".format(vendor))
    assert isinstance(vendor, SourcingVendor)
    return vendor


@with_db
def _get_ident(ident=None, session=None):
    if not ident:
        raise AttributeError('ident needs to be defined')
    if isinstance(ident, unicode):
        ident = str(ident)
    if not isinstance(ident, str):
        raise TypeError('ident needs to be a string, got'
                        ' {0} {1}'.format(type(ident), ident))
    return ident.strip()


@with_db
def _get_vpno_obj(vendor=None, ident=None, vpno=None,
                  mtype=None, session=None):

    if isinstance(vpno, VendorPartNumber):
        return vpno
    return get_vpno_obj(vendor=vendor, ident=ident,
                        vpno=vpno, mtype=mtype, session=session)


@with_db
def _create_map(vendor=None, ident=None, strategy=None, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)
    ident = _get_ident(ident=ident, session=session)

    mobj = VendorPartMap(ident=ident,
                         vendor_id=vendor.id,
                         strategy=strategy)
    session.add(mobj)
    session.flush()
    return mobj


_vendor_dbobj_cache = {}


# Core Sourcing Getters
@with_db
def get_vendor(name=None, create=False, session=None):
    if not name:
        raise ValueError("Name can't be none.")
    if name in _vendor_dbobj_cache.keys():
        return _vendor_dbobj_cache[name]
    try:
        vdbobj = session.query(SourcingVendor).filter_by(name=name).one()
        _vendor_dbobj_cache[name] = vdbobj
        return vdbobj
    except MultipleResultsFound:
        logger.warning("Found Multiple Objects for Vendor : " +
                       name)
    except NoResultFound:
        if create is True:
            obj = SourcingVendor(name=name)
            session.add(obj)
            return obj
        else:
            return None


@with_db
def get_vpno_obj(vendor=None, ident=None, vpno=None,
                 mtype=None, session=None):

    map_obj = get_map(vendor=vendor, ident=ident, session=session)

    q = session.query(VendorPartNumber)
    q = q.filter(VendorPartNumber.vpmap_id == map_obj.id)
    q = q.filter(VendorPartNumber.vpno == vpno)
    if mtype is not None:
        q = q.filter(VendorPartNumber.type == mtype)
    return q.one()


# Vendor Part Setters
@with_db
def populate_vpart_detail(vpno=None, vpart=None, session=None):
    assert isinstance(vpno, VendorPartNumber)
    from ..vendors import VendorPartBase
    assert isinstance(vpart, VendorPartBase)

    try:
        vpno.detail.vqtyavail = vpart.vqtyavail
        vpno.detail.manufacturer = vpart.manufacturer
        vpno.detail.mpartno = vpart.mpartno
        vpno.detail.vpartdesc = vpart.vpartdesc
        vpno.detail.vparturl = vpart.vparturl
        vpno.detail.pkgqty = vpart.pkgqty
    except AttributeError:
        vpno.detail = VendorPartDetail(
                vqtyavail=vpart.vqtyavail,
                manufacturer=vpart.manufacturer,
                mpartno=vpart.mpartno,
                vpartdesc=vpart.vpartdesc,
                pkgqty=vpart.pkgqty,
        )

    vpno.updated_at = arrow.utcnow()
    session.add(vpno)
    session.flush()


@with_db
def populate_vpart_detail_eln(vpno=None, vpart=None, session=None):
    assert isinstance(vpno, VendorPartNumber)
    from ..vendors import VendorElnPartBase
    assert isinstance(vpart, VendorElnPartBase)

    try:
        vpno.detail_eln.package = vpart.package
        vpno.detail_eln.datasheet = vpart.datasheet
    except AttributeError:
        vpno.detail_eln = VendorElnPartDetail(
                package=vpart.package,
                datasheet=vpart.datasheet,
        )

    session.add(vpno)
    session.flush()


@with_db
def clear_vpart_prices(vpno=None, session=None):
    assert isinstance(vpno, VendorPartNumber)
    vpno.prices = []
    session.add(vpno)
    session.flush()


@with_db
def populate_vpart_prices(vpno=None, vpart=None, session=None):
    assert isinstance(vpno, VendorPartNumber)
    from ..vendors import VendorPartBase
    assert isinstance(vpart, VendorPartBase)
    tprices = [(x.moq, str(x.unit_price.source_value), x.oqmultiple)
               for x in vpart.prices]

    prices_removal = []
    # TODO Currency types really need to switch to Decimal.
    for p in vpno.prices:
        pricetuple = (p.moq, p.price, p.oqmultiple)
        if pricetuple not in tprices:
            prices_removal.append(p)
        else:
            tprices.remove(pricetuple)

    for price in prices_removal:
        vpno.prices.remove(price)

    for price in tprices:
        vpno.prices.append(
            VendorPrice(
                moq=price[0],
                price=str(price[1]),
                oqmultiple=price[2],
            )
        )

    session.add(vpno)
    session.flush()


# Vendor Map Getters
@with_db
def get_map(vendor=None, ident=None, create=True, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)
    ident = _get_ident(ident=ident, session=session)

    q = session.query(VendorPartMap)
    q = q.filter(VendorPartMap.ident == ident)
    q = q.filter(VendorPartMap.vendor_id == vendor.id)
    try:
        return q.one()
    except NoResultFound:
        if create:
            return _create_map(vendor=vendor, ident=ident, session=session)
        else:
            raise
    except MultipleResultsFound:
        logger.error("Found multiple maps for {0} on {1}"
                     "".format(ident, vendor))
        raise


@with_db
def get_strategy(vendor=None, ident=None,  session=None):
    map_obj = get_map(vendor=vendor, ident=ident, session=session)
    return map_obj.strategy


@with_db
def get_time(vendor=None, ident=None,  session=None):
    try:
        map_obj = get_map(vendor=vendor, ident=ident,
                          create=False, session=session)
    except NoResultFound:
        return None
    if map_obj.updated_at:
        return map_obj.updated_at.timestamp
    else:
        return map_obj.created_at.timestamp


@with_db
def get_map_vpnos(vendor=None, ident=None, mtype=None, session=None):
    map_obj = get_map(vendor=vendor, ident=ident, session=session)

    q = session.query(VendorPartNumber.vpno)
    q = q.filter(VendorPartNumber.vpmap_id == map_obj.id)
    q = q.filter(VendorPartNumber.type == mtype)
    return [str(x.vpno) for x in q.all()]


@with_db
def get_amap_vpnos(vendor=None, ident=None, session=None):
    return get_map_vpnos(vendor=vendor, ident=ident,
                         mtype='auto', session=session)


@with_db
def get_umap_vpnos(vendor=None, ident=None,  session=None):
    return get_map_vpnos(vendor=vendor, ident=ident,
                         mtype='manual', session=session)


@with_db
def get_ident(vendor=None, vpno=None, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)

    q = session.query(VendorPartMap.ident)
    q = q.filter(VendorPartMap.vendor_id == vendor.id).join(VendorPartNumber)
    q = q.filter(VendorPartNumber.vpno == vpno)
    return str(q.one()[0])


@with_db
def get_vendor_idents(vendor=None, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)

    q = session.query(VendorPartMap)
    q = q.filter(VendorPartMap.vendor_id == vendor.id)
    q = q.filter(VendorPartMap.id == VendorPartNumber.vpmap_id)
    return q.all()


@with_db
def get_vendor_map_length(vendor=None, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)

    q = session.query(VendorPartNumber.id)
    q = q.join(VendorPartMap).join(SourcingVendor)
    q = q.filter(SourcingVendor.id == vendor.id)
    return int(q.count())


# Vendor Map Setters
@with_db
def set_strategy(vendor=None, ident=None, strategy=None, session=None):
    map_obj = get_map(vendor=vendor, ident=ident, session=session)
    map_obj.strategy = strategy
    map_obj.updated_at = arrow.utcnow()
    return map_obj


@with_db
def add_map_vpno(vendor=None, ident=None, vpno=None, mtype=None,
                 session=None):
    map_obj = get_map(vendor=vendor, ident=ident, session=session)

    vpno_obj = VendorPartNumber(vpno=vpno, type=mtype, vpmap_id=map_obj.id)
    session.add(vpno_obj)
    session.flush()
    return vpno_obj


@with_db
def remove_map_vpno(vendor=None, ident=None, vpno=None,
                    mtype=None, session=None):
    vendor = _get_vendor(vendor=vendor, session=session)
    ident = _get_ident(ident=ident, session=session)
    vpno_obj = _get_vpno_obj(vendor=vendor, ident=ident, vpno=vpno,
                             mtype=mtype, session=session)
    session.delete(vpno_obj)
    session.flush()


@with_db
def clear_map(vendor=None, ident=None, mtype=None, session=None):

    vpmap = get_map(vendor=vendor, ident=ident, session=session)
    if mtype is None:
        vpmap.vpnos = []
    else:
        vpmap.vpnos = [x for x in vpmap.vpnos if x.type != mtype]

    session.add(vpmap)
    session.flush()


@with_db
def set_map_vpnos(vendor=None, ident=None, vpnos=None,
                  mtype=None, session=None):
    vpmap = get_map(vendor=vendor, ident=ident, session=session)
    session.add(vpmap)

    # TODO Figure out why removal during the first pass breaks.
    vpnos_removal = []
    for vpno in vpmap.vpnos:
        if vpno.type == mtype and vpno.vpno in vpnos:
            vpnos.remove(vpno.vpno)
        else:
            vpnos_removal.append(vpno)

    for vpno in vpnos_removal:
        vpmap.vpnos.remove(vpno)

    for vpno in vpnos:
        vpmap.vpnos.append(
            VendorPartNumber(vpno=vpno, type=mtype)
        )

    vpmap.updated_at = arrow.utcnow()
    session.flush()


@with_db
def set_amap_vpnos(vendor=None, ident=None, vpnos=None, session=None):
    set_map_vpnos(vendor=vendor, ident=ident, vpnos=vpnos,
                  mtype='auto', session=session)


@with_db
def clear_amap(vendor=None, ident=None, session=None):
    clear_map(vendor=vendor, ident=ident, mtype='auto', session=session)


@with_db
def add_amap_vpno(vendor=None, ident=None, vpno=None, session=None):
    add_map_vpno(vendor=vendor, ident=ident,
                 vpno=vpno, mtype='auto', session=session)


@with_db
def remove_amap_vpno(vendor=None, ident=None, vpno=None, session=None):
    remove_map_vpno(vendor=vendor, ident=ident,
                    vpno=vpno, mtype='auto', session=session)


@with_db
def set_umap_vpnos(vendor=None, ident=None, vpnos=None, session=None):
    set_map_vpnos(vendor=vendor, ident=ident, vpnos=vpnos,
                  mtype='manual', session=session)


@with_db
def clear_umap(vendor=None, ident=None, session=None):
    clear_map(vendor=vendor, ident=ident, mtype='manual', session=session)


@with_db
def add_umap_vpno(vendor=None, ident=None, vpno=None, session=None):
    remove_map_vpno(vendor=vendor, ident=ident,
                    vpno=vpno, mtype='manual', session=session)


@with_db
def remove_umap_vpno(vendor=None, ident=None, vpno=None, session=None):
    remove_map_vpno(vendor=vendor, ident=ident,
                    vpno=vpno, mtype='manual', session=session)


# Maintenance Functions
def populate_vendors():
    logger.info("Populating Sourcing Vendors")
    for vendor in VENDORS_DATA:
        with get_session() as session:
            if not session.query(
                    exists().where(
                        SourcingVendor.name == vendor['name'])
            ).scalar():
                logger.info("Creating vendor entry for : " + vendor['name'])
                obj = SourcingVendor(name=vendor['name'],
                                     dname=vendor['dname'],
                                     type=vendor['type'],
                                     mapfile_base=vendor['name'],
                                     pclass=vendor['pclass'],
                                     status='active')
                session.add(obj)
            else:
                logger.debug("Found preexisting vendor entry for : " +
                             vendor['name'])
