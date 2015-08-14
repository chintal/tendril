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


import os
import yaml

from tendril.dox.labelmaker import manager

from tendril.utils.fs import import_
from tendril.utils.config import INSTANCE_ROOT

PRODUCTS_ROOT = os.path.join(INSTANCE_ROOT, 'products')
INSTANCE_PRODUCT_CLASSES_PATH = os.path.join(PRODUCTS_ROOT, 'infoclasses')
INSTANCE_PRODUCT_CLASSES = import_(INSTANCE_PRODUCT_CLASSES_PATH)


class ProductInfo(object):
    def __init__(self, infodict):
        self._infodict = infodict

    def labelinfo(self, sno):
        return sno, {}


class ProductBase(object):
    def __init__(self, fpath):
        self._fpath = fpath
        self._raw_data = None
        self._product_info = None
        self._cards = None
        self._cables = None
        self._labels = None

        self._load_product_info()

    def _load_product_info(self):
        with open(self._fpath, 'r') as f:
            self._raw_data = yaml.load(f)
        self._name = self._raw_data['name']
        self._cards = self._raw_data['cards']
        self._cables = self._raw_data['cables']
        self._labels = self._raw_data['labels']
        try:
            self._product_info = INSTANCE_PRODUCT_CLASSES.get_product_info_class(
                self._raw_data['productinfo']['line'],
                self._raw_data['productinfo']
            )
        except ImportError:
            self._product_info = ProductInfo(self._raw_data['productinfo'])

    @property
    def name(self):
        return self._name

    @property
    def cards(self):
        return self._cards

    @property
    def cables(self):
        return self._cables

    @property
    def labels(self):
        return self._labels

    def labelinfo(self, sno):
        return self._product_info.labelinfo(sno)

    def get_component_snos(self):
        pass


def get_folder_products(path):
    products = []
    files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    for f in files:
        if f.endswith('.product.yaml'):
            products.append(ProductBase(os.path.join(path, f)))
    return products


def gen_productlib(path=PRODUCTS_ROOT, recursive=True):
    products = []
    if recursive:
        for root, dirs, files in os.walk(path):
            products += get_folder_products(root)
    else:
        products = get_folder_products(path)
    return products

productlib = gen_productlib()


def generate_labels(product, sno):
    for l in product.labels:
        print "Generate label : ", l['type'], product.name, product.labelinfo(sno)
