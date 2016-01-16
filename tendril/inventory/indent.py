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

import os

from tendril.entityhub import serialnos
from tendril.entityhub.entitybase import EntityNotFound
from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.dox import docstore
from tendril.dox import labelmaker
from tendril.boms.outputbase import load_cobom_from_file

from tendril.utils.db import get_session


class IndentNotFound(EntityNotFound):
    pass


class InventoryIndent(object):
    def __init__(self, sno=None):
        self._sno = sno
        try:
            self.load_from_db()
            self._defined = True
        except IndentNotFound:
            self._cobom = None
            self._title = None
            self._desc = None
            self._prod_order_sno = None
            self._defined = False

    def create(self):
        pass

    def _generate_doc(self, outfolder):
        pass

    def _generate_cobom(self, outfolder):
        pass

    def _generate_labels(self, outfolder=None):
        for idx, line in enumerate(self._cobom.lines):
            labelmaker.manager.add_label(
                'IDT', line.ident, '.'.join([self._sno + 1, str(idx)]),
                qty=line.quantity)
        if outfolder and os.path.exists(outfolder):
            labelmaker.manager.generate_pdfs(outfolder, force=True)

    def _generate_docs(self, outfolder, register=True):
        pass

    def commit_to_db(self):
        pass

    def _get_indent_cobom(self):
        try:
            cobom_path = docstore.get_docs_list_for_sno_doctype(
                serialno=self._sno, doctype='PRODUCTION COBOM CSV', one=True
            ).path
        except SerialNoNotFound:
            raise IndentNotFound
        with docstore.docstore_fs.open(cobom_path, 'r') as f:
            cobom = load_cobom_from_file(
                f, os.path.splitext(os.path.split(cobom_path)[1])[0]
            )
        self._cobom = cobom

    def _get_prod_ord_sno_legacy(self):
        with get_session() as s:
            parents = serialnos.get_parent_serialnos(sno=self._sno, session=s)
            prod_sno = None
            for parent in parents:
                # TODO Change this to look for well defined production
                # orders or migrate to the new structure where the DB
                # maintains the correct mappings.
                if parent.parent.sno.startswith('PROD'):
                    prod_sno = parent.parent.sno
                    break
        if not prod_sno:
            self._prod_order_sno = None
        self._prod_order_sno = prod_sno

    def _get_title_legacy(self):
        from tendril.dox import production
        self._title = production.get_order_title(serialno=self._prod_order_sno)

    def _load_legacy(self):
        self._get_indent_cobom()
        self._get_prod_ord_sno_legacy()
        self._get_title_legacy()

    def load_from_db(self):
        if self._sno is None:
            raise ValueError
        self._load_legacy()

    @property
    def context(self):
        descriptors = self._cobom.descriptors
        context_parts = []
        for descriptor in descriptors:
            if descriptor.multiplier > 1:
                context_parts.append(' x'.join([descriptor.configname,
                                                descriptor.multiplier]))
            else:
                context_parts.append(descriptor.configname)
        return ', '.join(context_parts)

    @property
    def title(self):
        if self._title is not None:
            return self._title
        else:
            return self.prod_order.title

    @property
    def desc(self):
        if self._desc is not None:
            return self._desc
        else:
            return 'for {0} : {1}'.format(self._prod_order_sno, self.context)

    @property
    def lines(self):
        for idx, line in enumerate(self._cobom.lines):
            yield {'ident': line.ident, 'qty': line.quantity}

    @property
    def shortage(self):
        pass

    def report_shortage(self):
        pass

    @property
    def status(self):
        pass

    @property
    def serialno(self):
        return self._sno

    @property
    def root_orders(self):
        pass

    @property
    def prod_order(self):
        if self._prod_order_sno is not None:
            from tendril.production.order import ProductionOrder
            return ProductionOrder(self._prod_order_sno)

    @property
    def prod_order_sno(self):
        return self._prod_order_sno

    @property
    def supplementary_indents(self):
        pass

    @property
    def parent_indent(self):
        pass

    @property
    def root_indent(self):
        return

    @property
    def docs(self):
        pass

    def make_labels(self):
        self._generate_labels()

    def __repr__(self):
        return '<InventoryIndent {0} {1}>'.format(self._sno, self._title)
