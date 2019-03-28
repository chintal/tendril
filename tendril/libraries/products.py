# Copyright (C) 2015-2019 Chintalagiri Shashank
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

import os

from tendril.entities.products.prototype import ProductPrototypeBase
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


PRODUCTS_ROOT = os.path.join(INSTANCE_ROOT, 'products')


def get_folder_products(path):
    products = []

    files = [f for f in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]

    for f in files:
        if f.endswith('.product.yaml'):
            products.append(ProductPrototypeBase(os.path.join(path, f)))

    return products


def gen_productlib(path=PRODUCTS_ROOT, recursive=True):
    products = []
    if recursive:
        for root, dirs, files in os.walk(path):
            products += get_folder_products(root)
    else:
        products = get_folder_products(path)
    while None in products:
        products.remove(None)
    return products


productlib = gen_productlib()


def get_product_by_ident(ident):
    for product in productlib:
        if product.ident == ident:
            return product
    logger.error("Could not find product for ident : " + ident)


def get_product_by_core(core):
    for product in productlib:
        if product.core == core:
            return product
    logger.error("Could not find product for core : " + core)


def get_module_inclusion(modulename):
    rval = []
    for p in productlib:
        if modulename in p.module_listing.keys():
            rval.append((p, p.module_listing[modulename]))
    return rval


def get_product_calibformat(devicetype):
    info = get_product_by_core(devicetype)
    if info is not None:
        return info.calibformat
