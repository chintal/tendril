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

from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.dox.db.controller import DocumentNotFound
from .db.controller import IndentNotFound

from tendril.dox import docstore
from tendril.dox import labelmaker

from tendril.dox.indent import gen_stock_idt_from_cobom
from tendril.boms.outputbase import load_cobom_from_file

from .db import controller
from tendril.utils.db import get_session


class AuthChainNotValidError(Exception):
    pass


class InventoryIndent(object):
    def __init__(self, sno=None, verbose=True, session=None):
        self._sno = sno
        self._cobom = None
        self._title = None
        self._desc = None
        self._type = None
        self._status = None
        self._requested_by = None
        self._force = False
        self._rdate = None
        self._prod_order_sno = None
        self._root_order_sno = None
        try:
            self.load(verbose=verbose, session=session)
            self._defined = True
        except IndentNotFound:
            self._defined = False

    def create(self, cobom, title, desc=None, indent_type=None,
               requested_by=None, rdate=None, force=False):
        if self._defined is True and force is False:
            raise Exception("This inventory indent instance seems to be already "
                            "done. You can't 'create' it again.")
        self._cobom = cobom
        self._cobom.collapse_wires()
        self._title = title
        self._desc = desc
        self._type = indent_type
        self._requested_by = requested_by
        self._force = force
        self._rdate = rdate

    def define_auth_chain(self,  prod_order_sno=None, root_order_sno=None,
                          prod_order_scaffold=False, session=None):
        prod_order_sno = prod_order_sno or None
        if prod_order_sno is not None:
            if not serialnos.serialno_exists(sno=prod_order_sno,
                                             session=session):
                raise AuthChainNotValidError
            if not prod_order_scaffold:
                from tendril.production.order import ProductionOrder
                prod_order = ProductionOrder(prod_order_sno)
                if len(prod_order.indent_snos) and \
                        self.root_indent_sno not in prod_order.indent_snos:
                    raise AuthChainNotValidError
            self._prod_order_sno = prod_order_sno

        if root_order_sno is not None:
            if not serialnos.serialno_exists(sno=root_order_sno,
                                             session=session):
                raise AuthChainNotValidError
            self._root_order_sno = root_order_sno

        parents = self.auth_parent_snos
        if len(parents) == 0:
            raise AuthChainNotValidError

    def register_auth_chain(self, register=True, session=None):
        parents = self.auth_parent_snos
        if register is True:
            for parent in parents:
                serialnos.link_serialno(child=self.serialno,
                                        parent=parent,
                                        session=session)

    def process(self, session=None, **kwargs):
        if self._defined is True and self._force is False:
            raise Exception("This inventory indent instance seems to be already "
                            "done. You can't 'create' it again.")
        if session is None:
            with get_session() as session:
                return self._process(session=session, **kwargs)
        else:
            return self._process(session=session, **kwargs)

    def _process(self, outfolder=None, register=False,
                 verbose=True, session=None):
        self._process_shortage()
        self._dump_cobom(outfolder, register=register,
                         verbose=verbose, session=session)
        self._generate_doc(outfolder, register=register,
                           verbose=verbose, session=session)
        if register is True:
            self._sync_to_db(session=session)

    def _process_shortage(self):
        pass

    def _get_line_shortage(self):
        pass

    def _generate_doc(self, outfolder, register=False, verbose=True,
                      session=None):
        indentpath, indentsno = gen_stock_idt_from_cobom(
            outfolder, self.serialno, self.title, self.context, self._cobom,
            verbose=verbose
            )
        if register is True:
            docstore.register_document(
                serialno=self.serialno, docpath=indentpath,
                doctype='INVENTORY INDENT', efield=self.title,
                verbose=verbose, session=session
            )

    def _dump_cobom(self, outfolder, register=False,
                    verbose=True, session=None):
        with open(os.path.join(outfolder, 'cobom.csv'), 'w') as f:
            self._cobom.dump(f)
        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'cobom.csv'),
                    doctype='PRODUCTION COBOM CSV', efield=self.title,
                    verbose=verbose, session=session
            )

    def _generate_labels(self, label_manager=None):
        if label_manager is None:
            label_manager = labelmaker.manager
        for idx, line in enumerate(self._cobom.lines):
            label_manager.add_label(
                'IDT', line.ident, '.'.join([self._sno, str(idx)]),
                qty=line.quantity
            )

    def _sync_to_db(self, session=None):
        controller.upsert_inventory_indent(
            serialno=self._sno,
            title=self._title,
            desc=self._desc,
            itype=self._type,
            requested_by=self._requested_by,
            rdate=self._rdate,
            auth_parent_sno=self.auth_parent_snos[0],
            session=session
        )

    def _get_indent_cobom(self, session, verbose=True):
        try:
            cobom_path = docstore.get_docs_list_for_sno_doctype(
                serialno=self._sno, doctype='PRODUCTION COBOM CSV',
                one=True, session=session
            ).path
        except SerialNoNotFound:
            raise IndentNotFound
        except DocumentNotFound:
            raise IndentNotFound
        with docstore.docstore_fs.open(cobom_path, 'r') as f:
            cobom = load_cobom_from_file(
                f, os.path.splitext(os.path.split(cobom_path)[1])[0],
                verbose=verbose, generic=True
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
            prod_sno = None
        self._prod_order_sno = prod_sno

    def _get_title_legacy(self):
        if self._prod_order_sno is not None:
            self._title = self.prod_order.title

    def _load_legacy(self, session, verbose=True):
        self._get_indent_cobom(session=session, verbose=verbose)
        self._get_prod_ord_sno_legacy()
        self._get_title_legacy()

    def _resolve_auth_parents(self, auth_parent, verbose=True):
        # TODO Improve resolution. Handle multiple/complex parents.
        if auth_parent.sno.startswith('IDT-'):
            # This seems to be a parent indent
            assert self.root_indent_sno == auth_parent.sno
        elif auth_parent.sno.startswith('PROD-'):
            # This seems to be a production order
            self._prod_order_sno = auth_parent.sno
        else:
            self._root_order_sno = auth_parent.sno

    def _load_from_db(self, session, verbose=True):
        dbindent = controller.get_inventory_indent(serialno=self._sno,
                                                   session=session)
        self._title = dbindent.title
        self._desc = dbindent.desc
        self._type = dbindent.type
        self._requested_by = dbindent.requested_by.full_name
        self._rdate = dbindent.created_at
        self._status = dbindent.status
        auth_parent = dbindent.auth_parent
        self._resolve_auth_parents(auth_parent=auth_parent, verbose=verbose)
        self._get_indent_cobom(session=session, verbose=verbose)

    def _load(self, session, verbose=True):
        if self._sno is None:
            raise ValueError
        try:
            self._load_from_db(session, verbose=verbose)
            return
        except IndentNotFound:
            pass
        self._load_legacy(session=session, verbose=verbose)

    def load(self, verbose=True, session=None):
        if session is None:
            with get_session() as session:
                self._load(session=session, verbose=verbose)
        else:
            self._load(session=session, verbose=verbose)

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
    def requested_by(self):
        return self._requested_by

    @property
    def rdate(self):
        return self._rdate

    @property
    def cobom(self):
        return self._cobom

    @property
    def lines(self):
        for idx, line in enumerate(self._cobom.lines):
            yield {'ident': line.ident, 'qty': line.quantity}

    @property
    def status(self):
        return self._status

    @property
    def serialno(self):
        return self._sno

    @property
    def docs(self):
        return docstore.get_docs_list_for_serialno(serialno=self.serialno)

    def make_labels(self, label_manager=None):
        self._generate_labels(label_manager=label_manager)

    # Auth Chain
    @property
    def auth_parents(self):
        root_indent = self.root_indent
        if root_indent is not self:
            return [root_indent]
        prod_order = self.prod_order
        if prod_order is not None:
            return [prod_order]
        return self.root_orders

    @property
    def auth_parent_snos(self):
        if self.root_indent_sno != self.serialno:
            return [self.root_indent_sno]
        if self.prod_order_sno is not None:
            return [self.prod_order_sno]
        return self.root_orders

    @property
    def root_orders(self):
        return [self._root_order_sno]

    @property
    def root_order_snos(self):
        rval = []
        if self._root_order_sno is not None:
            if isinstance(self._root_order_sno, list):
                for sno in self._root_order_sno:
                    if sno not in rval:
                        rval.append(sno)
            else:
                if self._root_order_sno not in rval:
                    rval.append(self._root_order_sno)
        if self.root_indent_sno != self.serialno:
            for sno in self.root_indent.root_order_snos:
                if sno not in rval:
                    rval.append(sno)
        for sno in self.prod_order.root_order_snos:
            if sno not in rval:
                rval.append(sno)
        print rval
        return rval

    @property
    def prod_order(self):
        if self.prod_order_sno is not None:
            from tendril.production.order import ProductionOrder
            return ProductionOrder(sno=self.prod_order_sno)

    @property
    def prod_order_sno(self):
        if self._prod_order_sno is not None:
            return self._prod_order_sno
        elif self.root_indent_sno != self.serialno:
            return self.root_indent.prod_order_sno

    @property
    def root_indent_sno(self):
        if '.' in self.serialno:
            return self.serialno.split('.')[0]
        return self.serialno

    @property
    def root_indent(self):
        if self.root_indent_sno == self.serialno:
            return self
        return InventoryIndent(self.root_indent_sno)

    @property
    def supplementary_indent_snos(self):
        return [x.sno for x in
                docstore.controller.get_snos_by_document_doctype(
                    series=self.serialno + '.',
                    doctype='INVENTORY INDENT'
                )]

    @property
    def supplementary_indents(self):
        return [InventoryIndent(x) for x in self.supplementary_indent_snos]

    def __repr__(self):
        return '<InventoryIndent {0} {1}>'.format(self._sno, self._title)
