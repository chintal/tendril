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

import arrow
from six import iteritems

from tendril.boms.outputbase import CompositeOutputBom

from tendril.dox import docstore
from tendril.dox.production import gen_production_order
from tendril.dox.production import get_production_order_manifest_set

from tendril.entityhub import serialnos
from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.entityhub.entitybase import EntityNotFound
from tendril.entityhub.snomap import SerialNumberMap

from tendril.inventory.indent import InventoryIndent

from tendril.utils.db import get_session
from tendril.utils.files import yml as yaml
from tendril.utils.terminal import DummyProgressBar
from tendril.utils.terminal import TendrilProgressBar

from . import NothingToProduceError
from .actions import DeltaProductionAction
from .actions import CardProductionAction


class ProductionOrderNotFound(EntityNotFound):
    pass


class ProductionOrder(object):
    def __init__(self, sno=None, session=None):
        self._sno = sno
        self._card_actions = []
        self._delta_actions = []

        self._last_generated_at = None
        self._first_generated_at = None
        self._title = None
        self._desc = None
        self._indents = []
        self._root_order_snos = []
        self._sourcing_order_snos = []
        self._snomap_path = None
        self._snomap = None
        self._cards = {}
        self._deltas = []
        self._order_yaml_path = None
        self._yaml_data = None
        self._ordered_by = None

        self._force = None

        try:
            self.load(session=session)
            self._defined = True
        except ProductionOrderNotFound:
            self._defined = False

    def create(self, title=None, desc=None, cards=None, deltas=None,
               sourcing_order_snos=None, root_order_snos=None,
               ordered_by=None, order_yaml_path=None, snomap_path=None,
               force=False):
        # Load in the various parameters and such, creating the necessary
        # containers only.
        self._force = force
        if self._defined is True and self._force is False:
            raise Exception("This production order instance seems to be "
                            "already defined. You can't 'create' it again.")
        if order_yaml_path is not None:
            self._order_yaml_path = order_yaml_path
            with open(self._order_yaml_path, 'r') as f:
                self._yaml_data = yaml.load(f)
            self._load_order_yaml_data()
        if title:
            self._title = title
        if desc:
            self._desc = desc
        if cards:
            self._cards = cards
        if deltas:
            self._deltas = deltas
        if sourcing_order_snos:
            self._sourcing_order_snos = sourcing_order_snos
        if root_order_snos:
            self._root_order_snos = root_order_snos
        if ordered_by:
            self._ordered_by = ordered_by
        if snomap_path:
            self._snomap_path = snomap_path

        if len(self._cards) + len(self._deltas) == 0:
            raise NothingToProduceError

    def process(self, session=None, **kwargs):
        force = self._force
        if self._defined is True and force is False:
            raise Exception("This production order instance seems to be "
                            "already defined. You can't 'create' it again.")

        if session is None:
            with get_session() as session:
                return self._process(session=session, **kwargs)
        else:
            return self._process(session=session, **kwargs)

    def _process_indents(self, indent_sno=None, cobom=None, outfolder=None,
                         register=False, force=False, session=None):
        # Assume Indent is non-empty.
        # Create indent
        indent = InventoryIndent(indent_sno, verbose=False, session=session)
        indent.create(cobom, title="FOR {0}".format(self.serialno),
                      desc=None, indent_type='production',
                      requested_by=self._ordered_by, force=force)
        indent.define_auth_chain(prod_order_sno=self.serialno,
                                 session=session, prod_order_scaffold=True)
        indent.process(outfolder=outfolder, register=register,
                       verbose=False, session=session)
        self._indents.append(indent)

    def _process(self, outfolder=None, manifestsfolder=None,
                 label_manager=None, register=False, force=False,
                 pb_class=None, stacked_pb=False, leaf_pb=True,
                 session=None):
        self._force = force

        if pb_class is None:
            pb_class = TendrilProgressBar

        if stacked_pb is True:
            pb = pb_class(max=8)
        else:
            pb = DummyProgressBar(max=8)

        pb.next(note="Constructing Resources for Production Order Generation")

        if outfolder is None:
            if self._order_yaml_path is not None:
                outfolder = os.path.split(self._order_yaml_path)[0]
            else:
                raise AttributeError('Output folder needs to be defined')

        if manifestsfolder is None:
            manifestsfolder = os.path.join(outfolder, 'manifests')
            if not os.path.exists(manifestsfolder):
                os.makedirs(manifestsfolder)

        if self._sno is None:
            self._sno = serialnos.get_serialno(
                    series='PROD', efield=self._title,
                    register=register, session=session
            )

        # Create Snomap
        if self._snomap_path is not None:
            with open(self._snomap_path, 'r') as f:
                self._snomap = SerialNumberMap(yaml.load(f), self._sno)
        else:
            self._snomap = SerialNumberMap({}, self._sno)

        self._snomap.set_session(session=session)
        if register is True:
            self._snomap.enable_creation()

        indent_sno = self._snomap.get_sno('indentsno')
        if register is True:
            serialnos.link_serialno(child=indent_sno, parent=self.serialno,
                                    verbose=False, session=session)

        # Create cards and deltas and so forth
        pb.next(note="Constructing Production Order Actions")
        actions = self.card_actions + self.delta_actions

        pb.next(note="Executing Production Order Actions")
        for action in actions:
            if register is False:
                action.scaffold = True
            action.set_session(session=session)
            action.commit(
                outfolder=manifestsfolder, indent_sno=indent_sno,
                prod_ord_sno=self._sno, register=register, session=session,
                pb_class=pb_class, stacked_pb=stacked_pb, leaf_pb=leaf_pb,
            )

        self._snomap.disable_creation()

        pb.next(note="Constructing Composite Output BOM")
        cobom = CompositeOutputBom(self.bomlist)

        pb.next(note="Creating Indent(s)")
        self._process_indents(
            indent_sno=indent_sno, cobom=cobom, outfolder=outfolder,
            register=register, force=force, session=session
        )

        pb.next(note="Generating Production Order Document")
        # Make production order doc
        self._last_generated_at = arrow.utcnow().isoformat()
        if self._first_generated_at is None:
            self._first_generated_at = arrow.utcnow().isoformat()
        self._dump_order_yaml(outfolder=outfolder, register=register,
                              session=session)
        self._generate_doc(outfolder=outfolder, register=register,
                           session=session)

        pb.next(note="Generating Labels")
        self.make_labels(label_manager=label_manager, pb_class=pb_class,
                         stacked_pb=stacked_pb, leaf_pb=leaf_pb)

        pb.next(note="Finalizing Production Order")
        for action in actions:
            action.scaffold = False
            action.unset_session()
        self._snomap.dump_to_file(outfolder)
        self._snomap.unset_session()

        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'snomap.yaml'),
                    doctype='SNO MAP', efield=self.title,
                    verbose=False, session=session
            )
        pb.finish()
        self._defined = True

    def _generate_doc(self, outfolder=None, register=False, session=None):
        outpath = gen_production_order(
                outfolder, self.serialno, self._yaml_data, self.lines,
                sourcing_orders=self._sourcing_order_snos,
                verbose=False, root_orders=self.root_order_snos
        )
        if register is True:
            docstore.register_document(
                serialno=self.serialno, docpath=outpath,
                doctype='PRODUCTION ORDER', efield=self.title,
                verbose=False, session=session
            )

    def _build_yaml_data(self):
        if self._yaml_data is None:
            self._yaml_data = {}
        self._yaml_data['title'] = self._title
        self._yaml_data['desc'] = self._desc
        self._yaml_data['cards'] = self._cards
        self._yaml_data['deltas'] = self._deltas
        self._yaml_data['sourcing_order_snos'] = self._sourcing_order_snos
        self._yaml_data['root_order_snos'] = self._root_order_snos
        self._yaml_data['first_generated_at'] = self._first_generated_at
        self._yaml_data['last_generated_at'] = self._last_generated_at
        self._yaml_data['ordered_by'] = self._ordered_by
        self._yaml_data['prod_order_sno'] = self._sno

    def _dump_order_yaml(self, outfolder=None, register=False, session=None):
        self._build_yaml_data()
        with open(os.path.join(outfolder, 'order.yaml'), 'w') as f:
            f.write(yaml.dump(self._yaml_data, default_flow_style=False))
        if register is True:
            docstore.register_document(
                    serialno=self.serialno,
                    docpath=os.path.join(outfolder, 'order.yaml'),
                    doctype='PRODUCTION ORDER YAML',
                    verbose=False, efield=self.title,
                    session=session
            )

    def _load_snomap_legacy(self):
        # New form should construct directly from DB
        snomap_path = docstore.get_docs_list_for_sno_doctype(
            serialno=self._sno, doctype='SNO MAP', one=True
        ).path
        with docstore.docstore_fs.open(snomap_path, 'r') as f:
            snomap_data = yaml.load(f)
        self._snomap = SerialNumberMap(snomap_data, self._sno)

    def _load_order_yaml(self):
        try:
            order_path = docstore.get_docs_list_for_sno_doctype(
                serialno=self._sno, doctype='PRODUCTION ORDER YAML', one=True
            ).path
        except SerialNoNotFound:
            raise ProductionOrderNotFound
        with docstore.docstore_fs.open(order_path, 'r') as f:
            self._yaml_data = yaml.load(f)

    def _load_order_yaml_data(self):
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

        self._title = self._yaml_data.get('title')
        self._desc = self._yaml_data.get('desc', self._title)
        self._cards = self._yaml_data.get('cards', {})
        self._deltas = self._yaml_data.get('deltas', [])
        self._sourcing_order_snos = self._yaml_data.get('sourcing_orders', [])
        self._root_order_snos = self._yaml_data.get('root_orders', [])
        self._last_generated_at = self._yaml_data.get('last_generated_at',
                                                      None)
        self._first_generated_at = self._yaml_data.get('first_generated_at',
                                                       None)
        self._ordered_by = self._yaml_data.get('ordered_by', None)
        self._sno = self._yaml_data.get('prod_order_sno', self._sno)

    def _load_legacy(self):
        if self._sno is None:
            raise ProductionOrderNotFound
        self._load_order_yaml()
        self._load_order_yaml_data()
        self._load_snomap_legacy()

    def _load_from_db(self, session):
        raise NotImplementedError

    def load_from_db(self, session=None):
        if not session:
            with get_session() as session:
                self._load_from_db(session)
        else:
            self._load_from_db(session)

    def load(self, session=None):
        # Retrieve old production orders. If process is called on a loaded
        # production order, it'll overwrite whatever came before.
        try:
            self.load_from_db(session=session)
        except (ProductionOrderNotFound, NotImplementedError):
            pass
        self._load_legacy()

    @property
    def card_orders(self):
        return self._cards

    @property
    def card_actions(self):
        # This first len(..) bit is a litte dicey.
        if not len(self._card_actions):
            for card, qty in iteritems(self.card_orders):
                self._card_actions.append(
                    CardProductionAction(card, qty, self._snomap.get_sno)
                )
        return self._card_actions

    @property
    def card_boms(self):
        return [x.obom for x in self.card_actions]

    @property
    def cards(self):
        rval = []
        for action in self.card_actions:
            rval.extend(action.modules)
        return rval

    @property
    def card_lines(self):
        rval = []
        for action in self.card_actions:
            rval.extend(action.order_lines)
        return rval

    @property
    def delta_orders(self):
        return self._deltas

    @property
    def delta_actions(self):
        # This first len(..) bit is a litte dicey.
        if not len(self._delta_actions):
            for delta in self._deltas:
                self._delta_actions.append(
                        DeltaProductionAction(delta, force=self._force)
                )
        return self._delta_actions

    @property
    def delta_boms(self):
        return [x.obom for x in self.delta_actions]

    @property
    def deltas(self):
        # This will return the original card if the delta hasn't yet been
        # processed. Consider the inconsistency of this behavior and see what
        # to do about it.
        rval = []
        for action in self.delta_actions:
            rval.extend(action.modules)
        return rval

    @property
    def delta_lines(self):
        rval = []
        for action in self.delta_actions:
            rval.extend(action.order_lines)
        return rval

    @property
    def bomlist(self):
        return self.card_boms + self.delta_boms

    @property
    def lines(self):
        return self.card_lines + self.delta_lines

    @property
    def collated_manifests_pdf(self):
        return get_production_order_manifest_set(self.serialno)

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
        return None

    @property
    def root_order_snos(self):
        if isinstance(self._root_order_snos, list):
            return self._root_order_snos
        else:
            return [self._root_order_snos]

    @property
    def indent_snos(self):
        if 'indentsno' in self._snomap.map_keys():
            return self._snomap.mapped_snos('indentsno')
        else:
            return []

    @property
    def indents(self):
        if self._indents is None:
            from tendril.inventory.indent import InventoryIndent
            return [InventoryIndent(x) for x in self.indent_snos]
        else:
            return self._indents

    @property
    def docs(self):
        return docstore.get_docs_list_for_serialno(serialno=self.serialno)

    @property
    def status(self):
        return

    def make_labels(self, label_manager=None, include_all_indents=False,
                    include_main_indent=False, pb_class=None, leaf_pb=True,
                    **kwargs):
        cards = self.cards
        deltas = self.deltas

        if pb_class is None:
            pb_class = TendrilProgressBar
        if leaf_pb is True:
            pbmax = len(cards) + len(deltas)
            if include_all_indents is True:
                pbmax += len(self.indent_snos)
            elif include_main_indent is True:
                pbmax += 1
            pb = pb_class(max=pbmax)
        else:
            pb = None

        if include_all_indents is True:
            for indent in self.indents:
                if leaf_pb is True:
                    pb.next(
                        note='Labels for Indent {0}'.format(indent.serialno)
                    )
                indent.make_labels(label_manager=label_manager)
        elif include_main_indent is True:
            if len(self.indent_snos):
                indent = self.indents[-1]
                if leaf_pb is True:
                    pb.next(
                        note='Labels for Indent {0}'.format(indent.serialno)
                    )
                indent.make_labels(label_manager=label_manager)
        for card in cards:
            if leaf_pb is True:
                pb.next(note='Label for Card {0}'.format(card.refdes))
            card.make_labels(label_manager=label_manager)
        for delta in deltas:
            if leaf_pb is True:
                pb.next(note='Label for Delta {0}'.format(delta.refdes))
            delta.make_labels(label_manager=label_manager)
        if leaf_pb is True:
            pb.finish()

    def __repr__(self):
        return '<Production Order {0} {1}>'.format(self.serialno, self.title)
