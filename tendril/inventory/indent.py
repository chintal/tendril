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
Docstring for indent
"""


class InventoryIndent(object):
    def __init__(self, sno=None, title=None, desc=None, cobom=None):
        self._sno = sno
        self._cobom = cobom
        self._title = title
        self._desc = desc

    def create(self):
        pass

    def _generate_doc(self, outfolder):
        pass

    def _generate_cobom(self, outfolder):
        pass

    def _generate_labels(self, outfolder):
        pass

    def _generate_docs(self, outfolder, register=True):
        pass

    def commit_to_db(self):
        pass

    def load_from_db(self):
        pass

    @property
    def context(self):
        pass

    @property
    def title(self):
        return self._title

    @property
    def desc(self):
        return self._desc

    @property
    def lines(self):
        for idx, line in enumerate(self._cobom.lines):
            yield {'ident': line.ident, 'qty': line.quantity}

    @property
    def serialno(self):
        return self._sno

    @property
    def root_orders(self):
        return

    @property
    def prod_order(self):
        return

    @property
    def supplementary_indents(self):
        return

    @property
    def parent_indent(self):
        return

    @property
    def root_indent(self):
        return

    @property
    def docs(self):
        pass
