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
import warnings

from tendril.dox.labelmaker import manager

from tendril.utils.fsutils import import_
from tendril.utils.config import INSTANCE_ROOT
from tendril.conventions import status

from tendril.boms.outputbase import CompositeOutputBom
from tendril.boms.costingbase import HierachicalCostingBreakup
from tendril.boms.validate import ValidatableBase

from .modules import get_prototype_lib
from .prototypebase import PrototypeBase

from tendril.utils.files import yml as yaml
from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


PRODUCTS_ROOT = os.path.join(INSTANCE_ROOT, 'products')

INSTANCE_PRODUCT_CLASSES_PATH = os.path.join(PRODUCTS_ROOT, 'infoclasses')
INSTANCE_PRODUCT_CLASSES = import_(INSTANCE_PRODUCT_CLASSES_PATH)


class ProductInfo(ValidatableBase):
    def __init__(self, infodict, parent):
        super(ProductInfo, self).__init__()
        self._parent = parent
        self._infodict = infodict

    @property
    def ident(self):
        return self._parent.ident

    def labelinfo(self, sno):
        return sno, {}

    @property
    def line(self):
        # TODO Setup validation
        return self._infodict['line']

    @property
    def ptype(self):
        # TODO Setup validation
        return self._infodict['type']

    @property
    def desc(self):
        # TODO Setup validation
        return self._infodict['desc']

    @property
    def version(self):
        # TODO Setup validation
        try:
            return self._infodict['version']
        except KeyError:
            return None

    @property
    def status(self):
        # TODO Setup validation
        try:
            return status.get_status(self._infodict['status'])
        except KeyError:
            return status.get_status('Undefined')

    def _validate(self):
        pass


class ProductPrototypeBase(PrototypeBase):
    def __init__(self, fpath):
        super(ProductPrototypeBase, self).__init__()
        self._fpath = fpath
        self._raw_data = None
        self._product_info = None
        self._cards = None
        self._card_names = None
        self._cables = None
        self._cable_names = None
        self._labels = None
        self._boms = None
        self._obom = None
        self._sourcing_errors = None
        self._indicative_cost_hierarchical_breakup = None

        self._load_product_info()

    def _load_product_info(self):
        with open(self._fpath, 'r') as f:
            self._raw_data = yaml.load(f)
        self._name = self._raw_data['name']
        self._card_names = self._raw_data['cards']
        self._cable_names = self._raw_data['cables']
        self._labels = self._raw_data['labels']
        # TODO Some products don't have a viable core. Allowances must be made
        # Eg QM anf QI.
        self._core = self._raw_data['derive_sno_from']
        self._calibformat = self._raw_data['calibformat']
        try:
            self._product_info = \
                INSTANCE_PRODUCT_CLASSES.get_product_info_class(
                    self._raw_data['productinfo']['line'],
                    infodict=self._raw_data['productinfo'], parent=self
                )
        except ImportError:
            self._product_info = ProductInfo(
                infodict=self._raw_data['productinfo'], parent=self
            )

    @property
    def ident(self):
        if self.info.version:
            return "{0} v{1}".format(self.name, self.version)
        else:
            return self.name

    @property
    def version(self):
        return self._product_info.version

    @property
    def name(self):
        return self._name

    @property
    def info(self):
        return self._product_info

    @property
    def core(self):
        return self._core

    @staticmethod
    def _parse_listing(listing):
        rval = []
        for cname in listing:
            if cname is None:
                continue
            if isinstance(cname, dict):
                qty = cname['qty']
                try:
                    cname = cname['card']
                except KeyError:
                    cname = cname['cable']
            else:
                qty = 1
                cname = cname
            rval.append((cname, qty))
        return rval

    @property
    def card_listing(self):
        return self._parse_listing(self._card_names)

    @property
    def cable_listing(self):
        return self._parse_listing(self._cable_names)

    @property
    def module_listing(self):
        return {k: v for k, v in (self.card_listing + self.cable_listing)}

    @staticmethod
    def _get_modules(parsed_listing):
        rval = []
        pl = get_prototype_lib()
        for cname in parsed_listing:
            rval.append((pl[cname[0]], cname[1]))
        return rval

    @property
    def cards(self):
        if self._cards is None:
            self._cards = self._get_modules(self.card_listing)
        return self._cards

    @property
    def cables(self):
        if self._cables is None:
            self._cables = self._get_modules(self.cable_listing)
        return self._cables

    @property
    def labels(self):
        return self._labels

    def labelinfo(self, sno):
        return self._product_info.labelinfo(sno)

    @property
    def calibformat(self):
        return self._calibformat

    def get_component_snos(self):
        pass

    def make_labels(self, sno, label_manager=None):
        if label_manager is None:
            label_manager = manager
        labelinfo = self.labelinfo(sno)
        if labelinfo is not None:
            for l in self.labels:
                label_manager.add_label(
                    l['type'], self.name, labelinfo[0], **labelinfo[1]
                )

    @property
    def desc(self):
        return self._product_info.desc

    def _get_status(self):
        self._status = self._product_info.status

    def _construct_components(self):
        components = []
        for card, qty in self.cards:
            for i in range(qty):
                components.append(card)
        for cable, qty in self.cables:
            for i in range(qty):
                components.append(cable)
        return components

    def _construct_bom(self):
        self._boms = [x.obom for x in self._construct_components()]
        self._obom = CompositeOutputBom(self._boms, name=self.ident)
        self._obom.collapse_wires()

    @property
    def boms(self):
        if self._boms is None:
            self._construct_bom()
        return self._boms

    @property
    def obom(self):
        if self._obom is None:
            self._construct_bom()
        return self._obom

    @property
    def bom(self):
        raise NotImplementedError

    @property
    def indicative_cost(self):
        return self.obom.indicative_cost

    @property
    def sourcing_errors(self):
        if self._sourcing_errors is None:
            self._sourcing_errors = self.obom.sourcing_errors
        return self._sourcing_errors

    @property
    def indicative_cost_breakup(self):
        return self.obom.indicative_cost_breakup

    @property
    def indicative_cost_hierarchical_breakup(self):
        if self._indicative_cost_hierarchical_breakup is None:
            breakups = [x.indicative_cost_hierarchical_breakup
                        for x in self._construct_components()]
            if len(breakups) == 1:
                return breakups[0]
            rval = HierachicalCostingBreakup(self.ident)
            for breakup in breakups:
                rval.insert(breakup.name, breakup)
            self._indicative_cost_hierarchical_breakup = rval
        return self._indicative_cost_hierarchical_breakup

    @property
    def _changelogpath(self):
        raise NotImplementedError

    def _reload(self):
        raise NotImplementedError

    def _register_for_changes(self):
        raise NotImplementedError

    def _validate(self):
        pass


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


def get_product_calibformat(devicetype):
    info = get_product_by_core(devicetype)
    if info is not None:
        return info.calibformat


def generate_labels(product, sno, label_manager=None):
    warnings.warn("Deprecated use of generate_labels. Use the product "
                  "prototype object's make_labels function directly instead.",
                  DeprecationWarning)
    product.make_labels(sno, label_manager)


def get_module_inclusion(modulename):
    rval = []
    for p in productlib:
        if modulename in p.module_listing.keys():
            rval.append((p, p.module_listing[modulename]))
    return rval
