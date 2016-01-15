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

from .entitybase import EntityBase
from . import serialnos
from . import projects


class ModuleInstanceBase(EntityBase):
    validator = None

    def __init__(self, sno=None, ident=None, create=False):
        super(ModuleInstanceBase, self).__init__()
        self._customization = None
        self._ident = None
        if sno is not None:
            self.define(sno, ident, create)

    @property
    def ident(self):
        return self._ident

    @ident.setter
    def ident(self, value):
        if value not in projects.cards.keys():
            raise ValueError("Module {0} not recognized".format(value))
        if not self.validator(value):
            raise TypeError("Module {0} is not a not a valid module for {1}"
                            "".format(value, self.__class__))
        self._ident = value

    def define(self, sno, ident=None, create_new=False, register=True):
        self._refdes = sno
        if serialnos.serialno_exists(sno=sno):
            if create_new:
                raise ValueError("Serial Number {0} already exists, cannot be"
                                 " used to create a new instance".format(sno))
            db_ident = serialnos.get_serialno_efield(sno=self._refdes)
            if ident and db_ident != ident:
                raise ValueError("Module {0} seems to be a {1}, not {2}"
                                 "".format(sno, db_ident, ident))
            self.ident = db_ident
            self._defined = True
        else:
            if not create_new:
                raise ValueError("Serial Number {0} does not exist, and "
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


class EDAModuleInstanceBase(ModuleInstanceBase):
    @property
    def bom(self):
        from tendril.boms.electronics import import_pcb
        bomobj = import_pcb(projects.cards[self.ident])
        if self._customization is not None:
            raise NotImplementedError(
                    "gEDA Bom customization not yet implemented"
            )
        return bomobj.create_output_bom(configname=self.ident)


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


def get_module_instance(sno):
    modulename = serialnos.get_serialno_efield(sno=sno)
    if projects.check_module_is_card(modulename):
        return CardInstance(sno=sno)
    if projects.check_module_is_cable(modulename):
        return CableInstance(sno=sno)
