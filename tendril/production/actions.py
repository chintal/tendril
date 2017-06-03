#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2017 Chintalagiri Shashank
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
Docstring for actions
"""
from copy import deepcopy

from tendril.boms.outputbase import DeltaOutputBom
from tendril.dox import docstore
from tendril.dox.production import gen_delta_pcb_am, gen_pcb_am
from tendril.entityhub import serialnos
from tendril.entityhub.modules import get_module_instance
from tendril.entityhub.modules import get_module_prototype
from tendril.entityhub.modules import ModuleInstanceTypeMismatchError

from tendril.utils.terminal import TendrilProgressBar

from . import NothingToProduceError


class DeltaValidationError(Exception):
    pass


class ProductionActionBase(object):
    def __init__(self, *args, **kwargs):
        self._is_done = None
        self._scaffold = False
        self._session = kwargs.get('session')
        self.setup(*args, **kwargs)

    def set_session(self, session):
        self._session = session

    def unset_session(self):
        self._session = None

    @property
    def scaffold(self):
        return self._scaffold

    @scaffold.setter
    def scaffold(self, value):
        self._scaffold = value

    def setup(self, *args, **kwargs):
        raise NotImplementedError

    def commit(self, outfolder=None, indent_sno=None, prod_ord_sno=None,
               register=False, pb_class=None, stacked_pb=False, leaf_pb=True,
               session=None):
        raise NotImplementedError

    @property
    def obom(self):
        raise NotImplementedError

    @property
    def ident(self):
        raise NotImplementedError

    @property
    def refdes(self):
        raise NotImplementedError

    @property
    def modules(self):
        return [get_module_instance(x, self.ident,
                                    scaffold=self._scaffold,
                                    session=self._session)
                for x in self.refdes]

    @property
    def order_lines(self):
        raise NotImplementedError


class DeltaProductionAction(ProductionActionBase):
    def __init__(self, delta_order, force=False):
        self._sno = None
        self._original = None
        self._target = None
        self._orig_modulename = None
        self._target_modulename = None
        super(DeltaProductionAction, self).__init__(delta_order, force)

    def setup(self, delta_order, force):
        self._sno = delta_order['sno']
        self._orig_modulename = delta_order['orig-cardname']
        self._target_modulename = delta_order['target-cardname']
        if self._orig_modulename == self._target_modulename:
            raise DeltaValidationError
        try:
            try:
                self._original = get_module_instance(
                        self._sno, self._orig_modulename,
                        session=self._session,
                        scaffold=force
                )
                self._target = get_module_prototype(self._target_modulename)
                self._is_done = False
            except ModuleInstanceTypeMismatchError:
                self._target = get_module_instance(
                        self._sno, self._target_modulename,
                        session=self._session,
                        scaffold=force
                )
                self._original = get_module_prototype(self._orig_modulename)
                self._is_done = True
        except:
            # TODO a second delta on the same serial number will
            # make the first one fail. The entire delta architecture
            # may need to be thought through. Additionally, this
            # structure only handles deltas between cardnames, and
            # will go to hell in a handbasket if there are any
            # temporal changes to cards.
            raise DeltaValidationError

    def _generate_docs(self, manifestsfolder, indent_sno=None,
                       prod_ord_sno=None, register=False, session=None):
        dmpath = gen_delta_pcb_am(
                self._orig_modulename, self._target_modulename,
                outfolder=manifestsfolder, sno=self._sno,
                indentsno=indent_sno, productionorderno=prod_ord_sno
        )
        if register is True:
            docstore.register_document(serialno=self._sno, docpath=dmpath,
                                       doctype='DELTA ASSEMBLY MANIFEST',
                                       session=session)

    def commit(self, outfolder=None, indent_sno=None, prod_ord_sno=None,
               register=False, pb_class=None, stacked_pb=False, leaf_pb=True,
               session=None):
        if self._is_done is True:
            raise NothingToProduceError
        self._generate_docs(outfolder, indent_sno, prod_ord_sno,
                            register, session)
        if register is True:
            serialnos.set_serialno_efield(
                sno=self._sno, efield=self._target_modulename,
                session=session
            )
            serialnos.link_serialno(
                child=self._sno, parent=prod_ord_sno, session=session
            )
            self._original = get_module_prototype(self._orig_modulename)
            self._target = get_module_instance(self._sno,
                                               self._target_modulename,
                                               session=session)
            self._is_done = True

    @property
    def delta_bom(self):
        original_obom = self._original.obom
        target_obom = self._target.obom
        delta_obom = DeltaOutputBom(original_obom, target_obom)
        return delta_obom.additions_bom

    @property
    def obom(self):
        return self.delta_bom

    @property
    def ident(self):
        return '{0} -> {1}'.format(self._original.ident, self._target.ident)

    @property
    def refdes(self):
        return [self._sno]

    @property
    def modules(self):
        return [get_module_instance(x, self._target_modulename,
                                    session=self._session)
                for x in self.refdes]

    @property
    def order_lines(self):
        target_prototype = get_module_prototype(self._target_modulename)
        ctx = target_prototype.strategy
        ctx['ident'] = self._target_modulename
        ctx['is_delta'] = True
        ctx['desc'] = self.ident
        ctx['sno'] = self._sno
        return [ctx]

    def __repr__(self):
        if self._is_done is True:
            done = 'DONE'
        elif self._is_done is False:
            done = 'NOT DONE'
        else:
            done = 'NOT DEFINED'
        return '<DeltaProductionAction {0} {1} {2}>'.format(
            self.ident, self.refdes, done
        )


class CardProductionAction(ProductionActionBase):
    def __init__(self, *args, **kwargs):
        self._ident = None
        self._qty = None
        self._prototype = None
        self._snos = None
        super(CardProductionAction, self).__init__(*args, **kwargs)

    def setup(self, card, qty, snofunc):
        self._ident = card
        self._prototype = get_module_prototype(card)
        self._qty = qty
        self._snos = []
        for idx in range(self._qty):
            # Registration is dependent on the snofunc, and consequently
            # the state of the corresponding snomap.
            self._snos.append(snofunc(self.ident))

    def _generate_am(self, manifestsfolder, sno, prod_ord_sno, indent_sno,
                     verbose=True, register=False, session=None):
        ampath = gen_pcb_am(self._ident, manifestsfolder, sno,
                            productionorderno=prod_ord_sno,
                            indentsno=indent_sno, scaffold=self.scaffold,
                            verbose=verbose, session=session)
        if register is True:
            docstore.register_document(serialno=sno, docpath=ampath,
                                       doctype='ASSEMBLY MANIFEST',
                                       verbose=verbose, session=session)

    def commit(self, outfolder=None, indent_sno=None, prod_ord_sno=None,
               register=False, pb_class=None, stacked_pb=False, leaf_pb=True,
               session=None):
        # Serial numbers will already have been written in.
        if self._prototype.strategy['genmanifest'] is True:

            if pb_class is None:
                pb_class = TendrilProgressBar
            if leaf_pb is True:
                pb = pb_class(max=len(self.refdes))
                verbose = False
            else:
                pb = None
                verbose = True

            msg = "Generating Manifests and Linking for {0}".format(self.ident)
            print(msg)

            for card in self.modules:
                self._generate_am(
                    outfolder, card.refdes, prod_ord_sno, indent_sno,
                    verbose=verbose, register=register, session=session
                )
                if register is True:
                    serialnos.link_serialno(
                        child=card.refdes, parent=prod_ord_sno,
                        verbose=verbose, session=session
                    )
                if leaf_pb is True:
                    pb.next(note=card.refdes)
            if leaf_pb is True:
                pb.finish()

    @property
    def obom(self):
        obom = self._prototype.bom.create_output_bom(self.ident)
        obom.multiply(self._qty)
        return obom

    @property
    def ident(self):
        return self._ident

    @property
    def refdes(self):
        return self._snos

    @property
    def order_lines(self):
        rval = []
        base_ctx = self._prototype.strategy
        base_ctx['ident'] = self.ident
        base_ctx['is_delta'] = False
        for card in self.modules:
            ctx = deepcopy(base_ctx)
            ctx['sno'] = card.refdes
            rval.append(ctx)
        return rval
