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
from tendril.dox.db.controller import DocumentNotFound

from tendril.dox import docstore
from tendril.dox import labelmaker

from tendril.dox.indent import gen_stock_idt_from_cobom
from tendril.boms.outputbase import load_cobom_from_file

from tendril.utils.db import get_session


class IndentNotFound(EntityNotFound):
    pass


class InventoryIndent(object):
    def __init__(self, sno=None, session=None):
        self._sno = sno
        try:
            self.load_from_db(session=session)
            self._defined = True
        except IndentNotFound:
            self._cobom = None
            self._title = None
            self._desc = None
            self._prod_order_sno = None
            self._requested_by = None
            self._defined = False

    def create(self, cobom, title, desc=None, prod_order_sno=None,
               requested_by=None, force=False):
        if self._defined is True and force is False:
            raise Exception("This inventory indent instance seems to be already "
                            "done. You can't 'create' it again.")
        self._cobom = cobom
        self._cobom.collapse_wires()
        self._title = title
        self._desc = desc
        self._prod_order_sno = prod_order_sno
        self._requested_by = requested_by
        self._force = force

    def process(self, session=None, **kwargs):
        if self._defined is True and self._force is False:
            raise Exception("This inventory indent instance seems to be already "
                            "done. You can't 'create' it again.")
        if session is None:
            with get_session() as session:
                return self._process(session=session, **kwargs)
        else:
            return self._process(session=session, **kwargs)

    def _process(self, outfolder=None, register=False, session=None):
        self._process_shortage()
        self._dump_cobom(outfolder, register=register, session=session)
        self._generate_doc(outfolder, register=register, session=session)

    def _process_shortage(self):
        pass

    def _get_line_shortage(self):
        pass

    def _generate_doc(self, outfolder, register=False, session=None):
        indentpath, indentsno = gen_stock_idt_from_cobom(
            outfolder, self.serialno, self.title, self.context, self._cobom
            )
        if register is True:
            docstore.register_document(
                serialno=self.serialno, docpath=indentpath,
                doctype='INVENTORY INDENT', efield=self.title,
                session=session
            )

    def _dump_cobom(self, outfolder, register=False, session=None):
        with open(os.path.join(outfolder, 'cobom.csv'), 'w') as f:
            self._cobom.dump(f)
        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'cobom.csv'),
                    doctype='PRODUCTION COBOM CSV', efield=self.title,
                    session=session
            )

    def _generate_labels(self, label_manager=None):
        if label_manager is None:
            from tendril.dox.labelmaker import manager
            label_manager = manager
        for idx, line in enumerate(self._cobom.lines):
            label_manager.add_label(
                'IDT', line.ident, '.'.join([self._sno, str(idx)]),
                qty=line.quantity
            )

    def _get_indent_cobom(self, session=None):
        try:
            cobom_path = docstore.get_docs_list_for_sno_doctype(
                serialno=self._sno, doctype='PRODUCTION COBOM CSV', one=True,
                session=session
            ).path
        except SerialNoNotFound:
            raise IndentNotFound
        except DocumentNotFound:
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
        self._title = self.prod_order.title

    def _load_legacy(self, session=None):
        self._get_indent_cobom(session=session)
        self._get_prod_ord_sno_legacy()
        self._get_title_legacy()

    def load_from_db(self, session=None):
        if self._sno is None:
            raise ValueError
        self._load_legacy(session=session)

    @property
    def context(self):
        descriptors = self._cobom.descriptors
        context_parts = []
        for descriptor in descriptors:
            if descriptor.multiplier > 1:
                context_parts.append(' x'.join([descriptor.configname,
                                                str(descriptor.multiplier)]))
            else:
                context_parts.append(descriptor.configname)
        return ', '.join(context_parts)

    @property
    def title(self):
        if self._title is not None:
            return self._title
        elif self.prod_order_sno is not None:
            return self.prod_order.title

    @property
    def desc(self):
        if self._desc is not None:
            return self._desc
        else:
            return 'for {0} : {1}'.format(self._prod_order_sno, self.context)

    @property
    def cobom(self):
        return self._cobom

    @property
    def lines(self):
        for idx, line in enumerate(self._cobom.lines):
            yield {'ident': line.ident, 'qty': line.quantity}

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
    def root_order_snos(self):
        return self.prod_order.root_order_snos

    @property
    def prod_order(self):
        if self._prod_order_sno is not None:
            from tendril.production.order import ProductionOrder
            return ProductionOrder(self._prod_order_sno)

    @property
    def prod_order_sno(self):
        return self._prod_order_sno

    @staticmethod
    def get_root_indent_sno(serialno):
        if '.' in serialno:
            serialno = serialno.split['.'][0]
        return serialno

    @property
    def root_indent_sno(self):
        return self.get_root_indent_sno(self.serialno)

    @property
    def root_indent(self):
        return InventoryIndent(self.root_indent_sno)

    @property
    def supplementary_indent_snos(self):
        return docstore.controller.get_snos_by_document_doctype(
                series=self.serialno + '.', doctype='INVENTORY INDENT'
        )

    @property
    def supplementary_indents(self):
        return [InventoryIndent(x) for x in self.supplementary_indent_snos]

    @property
    def docs(self):
        return docstore.get_docs_list_for_serialno(serialno=self.serialno)

    def make_labels(self, label_manager=None):
        self._generate_labels(label_manager=label_manager)

    def __repr__(self):
        return '<InventoryIndent {0} {1}>'.format(self._sno, self._title)
