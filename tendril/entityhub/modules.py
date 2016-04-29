#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
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
Docstring for modules
"""

import os
from copy import deepcopy

from tendril.boms.electronics import EntityElnBom
from tendril.gedaif.conffile import ConfigsFile
from tendril.utils import log
from tendril.utils.parsers import changelog
from . import projects
from . import serialnos
from .db.controller import SerialNoNotFound
from .entitybase import EntityBase

logger = log.get_logger(__name__, log.DEFAULT)


class ModuleNotRecognizedError(Exception):
    pass


class ModuleTypeError(Exception):
    pass


class ModuleInstanceTypeMismatchError(Exception):
    pass


class ContextualConfigError(Exception):
    pass


class ModuleStrategyParseError(ContextualConfigError):
    pass


class ModulePrototypeBase(object):
    validator = None

    def __init__(self, modulename):
        self._modulename = None
        self._configs = None
        self._bom = None
        self._obom = None
        self._status = None
        self._strategy = None
        self._changelog = None
        self.ident = modulename

    @property
    def ident(self):
        return self._modulename

    @ident.setter
    def ident(self, value):
        if value not in projects.cards.keys():
            raise ModuleNotRecognizedError(
                    "Module {0} not recognized".format(value))
        if not self.validator(value):
            raise ModuleTypeError("Module {0} is not a not a valid module for "
                                  "{1}".format(value, self.__class__))
        self._modulename = value
        try:
            self._strategy = self._get_production_strategy()
        except KeyError:
            raise ModuleStrategyParseError(
                "Missing Key(s) loading strategy for {}"
                "".format(self.ident)
            )
        self._get_changelog()

    @property
    def status(self):
        if self._status is None:
            self._get_status()
        return self._status

    @property
    def strategy(self):
        if self._strategy is None:
            try:
                self._strategy = self._get_production_strategy()
            except KeyError:
                raise ModuleStrategyParseError(
                    "Missing Key(s) loading strategy for {}"
                    "".format(self.ident)
                )
        return self._strategy

    @property
    def changelog(self):
        if self._changelog is None:
            self._get_changelog()
        return self._changelog

    def _get_production_strategy(self):
        raise NotImplementedError

    def _get_status(self):
        raise NotImplementedError

    @property
    def _changelogpath(self):
        raise NotImplementedError

    def _get_changelog(self):
        try:
            self._changelog = changelog.ChangeLog(self._changelogpath)
        except changelog.ChangeLogNotFoundError:
            pass

    def make_labels(self, sno, label_manager=None):
        raise NotImplementedError


class EDAModulePrototypeBase(ModulePrototypeBase):
    @property
    def configs(self):
        if not self._configs:
            self._configs = ConfigsFile(self.projfolder)
        return self._configs

    @property
    def bom(self):
        if not self._bom:
            self._bom = EntityElnBom(self.configs)
            self._bom.configure_motifs(self.ident)
        return self._bom

    @property
    def obom(self):
        if not self._obom:
            self._obom = self.bom.create_output_bom(configname=self.ident)
        return self._obom

    def _get_status(self):
        raise NotImplementedError

    def _get_production_strategy(self):
        rval = {}
        configdata = self.configs.rawconfig
        if configdata['documentation']['am'] is True:
            # Assembly manifest should be used
            rval['prodst'] = "@AM"
            rval['genmanifest'] = True
        elif configdata['documentation']['am'] is False:
            # No Assembly manifest needed
            rval['prodst'] = "@THIS"
            rval['genmanifest'] = False
        if configdata['productionstrategy']['testing'] == 'normal':
            # Normal test procedure, Test when made
            rval['testst'] = "@NOW"
        if configdata['productionstrategy']['testing'] == 'lazy':
            # Lazy test procedure, Test when used
            rval['testst'] = "@USE"
        if configdata['productionstrategy']['labelling'] == 'normal':
            # Normal test procedure, Label when made
            rval['lblst'] = "@NOW"
        if configdata['productionstrategy']['testing'] == 'lazy':
            # Lazy test procedure, Label when used
            rval['lblst'] = "@USE"
        rval['genlabel'] = False
        rval['labels'] = []
        if isinstance(configdata['documentation']['label'], dict):
            for k in sorted(configdata['documentation']['label'].keys()):
                rval['labels'].append(
                    {'code': k,
                     'ident': self.ident + '.' + configdata['label'][k]}
                )
            rval['genlabel'] = True
        elif isinstance(configdata['documentation']['label'], str):
            rval['labels'].append(
                {'code': configdata['documentation']['label'],
                 'ident': self.ident}
            )
            rval['genlabel'] = True
        return rval

    def make_labels(self, sno, label_manager=None):
        # This does not check whether the sno is valid and correct and
        # so on. This should therefore not be called directly, but instead
        # the instance's makelabel function should be used.
        if label_manager is None:
            from tendril.dox.labelmaker import manager
            label_manager = manager
        if self.strategy['genlabel'] is True:
            for label in self.strategy['labels']:
                label_manager.add_label(
                    label['code'], label['ident'], sno
                )

    @property
    def _changelogpath(self):
        return os.path.join(self.projfolder, 'ChangeLog')

    @property
    def projfolder(self):
        return projects.cards[self.ident]


class CardPrototype(EDAModulePrototypeBase):
    validator = staticmethod(projects.check_module_is_card)

    @property
    def pcbname(self):
        return self.bom.configurations.rawconfig['pcbname']

    def _get_status(self):
        self._status = self.configs.status_config(self.ident)

    def __repr__(self):
        return '<CardPrototype {0}>'.format(self.ident)


class CablePrototype(EDAModulePrototypeBase):
    validator = staticmethod(projects.check_module_is_cable)

    def __repr__(self):
        return '<CablePrototype {0}>'.format(self.ident)

    def _get_status(self):
        return None

    @property
    def cblname(self):
        return self.bom.configurations.rawconfig['cblname']


def get_module_prototype(modulename):
    if projects.check_module_is_card(modulename):
        return CardPrototype(modulename)
    if projects.check_module_is_cable(modulename):
        return CablePrototype(modulename)


class ModuleInstanceBase(EntityBase):
    validator = None

    def __init__(self, sno=None, ident=None, create=False,
                 scaffold=False, session=None):
        super(ModuleInstanceBase, self).__init__()
        self._prototype = None
        self._obom = None
        self._customization = None
        self._ident = None
        if sno is not None:
            self.define(sno, ident, create,
                        scaffold=scaffold, session=session)

    @property
    def ident(self):
        return self._ident

    @ident.setter
    def ident(self, value):
        if value not in projects.cards.keys():
            raise ModuleNotRecognizedError("Module {0} not recognized"
                                           "".format(value))
        if not self.validator(value):
            raise ModuleTypeError("Module {0} is not a not a valid module for"
                                  " {1}".format(value, self.__class__))
        self._ident = value

    def define(self, sno, ident=None, create_new=False,
               register=True, scaffold=False, session=None):
        self._refdes = sno
        if scaffold is True:
            self.ident = ident
            self._defined = True
            return
        if serialnos.serialno_exists(sno=sno, session=session):
            if create_new:
                raise ValueError("Serial Number {0} already exists, cannot be"
                                 " used to create a new instance".format(sno))
            db_ident = serialnos.get_serialno_efield(sno=self._refdes,
                                                     session=session)
            if ident and db_ident != ident:
                raise ModuleInstanceTypeMismatchError(
                        "Module {0} seems to be a {1}, not {2}"
                        "".format(sno, db_ident, ident)
                )
            self.ident = db_ident
            self._defined = True
        else:
            if not create_new:
                raise SerialNoNotFound("Serial Number {0} does not exist, and"
                                       "creation of a new instance is not "
                                       "requested".format(sno))
            else:
                self.ident = ident
                self._defined = True
                raise NotImplementedError(
                        "Registration of serial number of modules should be "
                        "done at the production order level. Registering "
                        "module instances directly is not supported. Once you"
                        " have the serial numbers registered, you can come "
                        "here to fill in the rest.")

    @property
    def prototype(self):
        if self._prototype is None:
            self._prototype = get_module_prototype(self._ident)
        return self._prototype


class EDAModuleInstanceBase(ModuleInstanceBase):
    @property
    def obom(self):
        if self._obom is None:
            bomobj = deepcopy(self.prototype.bom)
            if self._customization is not None:
                raise NotImplementedError(
                        "gEDA Bom customization not yet implemented"
                )
            self._obom = bomobj.create_output_bom(configname=self.ident)
        return self._obom

    def make_labels(self, label_manager=None):
        self.prototype.make_labels(self._refdes, label_manager=label_manager)

    @property
    def projfolder(self):
        return self._prototype.projfolder


class CardInstance(EDAModuleInstanceBase):
    validator = staticmethod(projects.check_module_is_card)

    def __repr__(self):
        if self._customization is not None:
            customized = ' Customized'
        else:
            customized = ''
        return "<CardInstance {0} {1}{2}>".format(
                self.ident, self.refdes, customized
        )

    @property
    def pcbname(self):
        return self._prototype.pcbname


class CableInstance(EDAModuleInstanceBase):
    validator = staticmethod(projects.check_module_is_cable)

    def __repr__(self):
        if self._customization is not None:
            customized = ' Customized'
        else:
            customized = ''
        return '<CableInstance {0} {1}{2}>'.format(
                self.ident, self.refdes, customized
        )

    @property
    def cblname(self):
        return self._prototype.cblname


def get_module_instance(sno, ident=None, scaffold=False, session=None):
    if not scaffold:
        modulename = serialnos.get_serialno_efield(sno=sno,
                                                   session=session)
    else:
        modulename = ident
    if projects.check_module_is_card(modulename):
        return CardInstance(sno=sno, ident=ident,
                            scaffold=scaffold, session=session)
    if projects.check_module_is_cable(modulename):
        return CableInstance(sno=sno, ident=ident,
                             scaffold=scaffold, session=session)


def generate_prototype_lib():
    lprototypes = {}
    for card, folder in projects.cards.iteritems():
        if projects.check_module_is_card(card):
            lprototypes[card] = CardPrototype(card)
        elif projects.check_module_is_cable(card):
            lprototypes[card] = CablePrototype(card)
    return lprototypes

prototypes = generate_prototype_lib()
