#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for order
"""

import os
import yaml

from tendril.dox import docstore
from tendril.dox import labelmaker

from tendril.entityhub.snomap import SerialNumberMap


class ProductionOrder(object):
    def __init__(self, sno=None):
        self._sno = sno
        try:
            self.load_from_db()
            self._defined = True
        except:
            self._title = None
            self._desc = None
            self._indents = []
            self._root_order_snos = []
            self._sourcing_order_snos = []
            self._snomap = None
            self._defined = False
            self._cards = None
            self._deltas = None

    def create(self):
        # Load in the various parameters and such, creating the necessary
        # containers only.
        pass

    def process(self):
        # Actually process the order and generate downstream documentation.
        pass

    def _process_order(self):
        pass

    def _generate_doc(self, outfolder=None):
        pass

    def _generate_snomap(self, outfolder=None):
        pass

    def _generate_manifests(self, outfolder=None):
        pass

    def _generate_labels(self, outfolder=None):
        pass

    def _generate_docs(self, outfolder, register=True):
        pass

    def commit_to_db(self):
        pass

    def _get_indent_snos_legacy(self):
        pass

    def _get_root_order_snos_legacy(self):
        pass

    def _load_snomap_legacy(self):
        # New form should construct directly from DB
        snomap_path = docstore.get_docs_list_for_sno_doctype(
            serialno=self._sno, doctype='SNO MAP'
        )[0].path
        with docstore.docstore_fs.open(snomap_path, 'r') as f:
            snomap_data = yaml.load(f)
        self._snomap = SerialNumberMap(snomap_data, self._sno)

    def _load_order_yaml(self):
        order_path = docstore.get_docs_list_for_sno_doctype(
            serialno=self._sno, doctype='PRODUCTION ORDER YAML'
        )[0].path
        with docstore.docstore_fs.open(order_path, 'r') as f:
            order_yaml_data = yaml.load(f)

            # Following keys are ignored / deprecated:
            #  - register
            #  - halt_on_shortage
            #  - include_refbom_for_no_am
            #  - force_labels
            #
            # All of these are more about run control than defining
            # the production order, and thus are left to the run control
            # code to work out. The order.yaml files are now only
            # going to define things that are not temporally transient.

            self._title = order_yaml_data.pop('title')
            self._desc = order_yaml_data.pop('title', None)
            self._cards = order_yaml_data.pop('cards', {})
            self._deltas = order_yaml_data.pop('deltas', [])
            self._sourcing_order_snos = order_yaml_data.pop('sourcing_orders',
                                                            [])
            self._root_orders_snos = order_yaml_data.pop('root_orders', [])

    def _load_legacy(self):
        self._load_order_yaml()
        self._load_snomap_legacy()

    def load_from_db(self):
        # Retrieve old production orders. If process is called on a loaded
        # production order, it'll overwrite whatever came before.
        self._load_legacy()

    @property
    def card_orders(self):
        return self._cards

    @property
    def cards(self):
        pass

    @property
    def delta_orders(self):
        return self._deltas

    @property
    def deltas(self):
        pass

    @property
    def title(self):
        return self._title

    @property
    def desc(self):
        if self._desc is None:
            return 'Production Order for {0}'.format(self._title)
        else:
            return self._desc

    @property
    def serialno(self):
        return self._sno

    @property
    def root_orders(self):
        pass

    @property
    def root_order_snos(self):
        return self._root_order_snos

    @property
    def indents(self):
        from tendril.inventory.indent import InventoryIndent
        return [InventoryIndent(x) for x in self.indent_snos]

    @property
    def indent_snos(self):
        if 'indentsno' in self._snomap.map_keys():
            return self._snomap.mapped_snos('indentsno')
        else:
            return []

    @property
    def docs(self):
        return

    @property
    def status(self):
        return

    def __repr__(self):
        return '<Production Order {0} {1}>'.format(self.serialno, self.title)
