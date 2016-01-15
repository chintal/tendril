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

from tendril.dox import labelmaker


class ProductionOrder(object):
    def __init__(self, sno=None):
        self._sno = sno
        try:
            pass
        except:
            self._title = None
            self._desc = None
            self._indents = []
            self._root_orders = []
            self._snomap = None

    def create(self):
        pass

    def _generate_doc(self, outfolder=None):
        pass

    def _generate_manifests(self, outfolder=None):
        pass

    def _generate_labels(self, outfolder=None):
        pass

    def _generate_docs(self, outfolder, register=True):
        pass

    def commit_to_db(self):
        pass

    def _load_order_yaml(self):
        pass

    def _load_legacy(self):
        self._load_order_yaml()

    def load_from_db(self):
        self._load_legacy()

    @property
    def title(self):
        pass

    @property
    def desc(self):
        pass

    @property
    def root_orders(self):
        return

    @property
    def indents(self):
        return

    @property
    def docs(self):
        return

    @property
    def status(self):
        return
