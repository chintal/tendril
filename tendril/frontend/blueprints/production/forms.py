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
Docstring for forms
"""


from flask_wtf import Form
from wtforms.fields import StringField
from wtforms.fields import SelectField
from wtforms.fields import BooleanField
from wtforms.fields import FieldList
from wtforms.fields import FormField

from wtforms.validators import InputRequired
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import AnyOf
from wtforms.validators import ValidationError

from wtforms_components import read_only

from flask_user import current_user

from tendril.frontend.parts.forms import DateInputField
from tendril.frontend.parts.forms import NewSerialNumberForm
from tendril.frontend.parts.forms import user_auth_check

from tendril.entityhub import serialnos
from tendril.entityhub.db.controller import SerialNoNotFound
from tendril.entityhub.projects import cards
# from tendril.inventory.electronics import get_recognized_repr


class ModuleQtyForm(Form):
    # TODO add customization field
    ident = StringField(label='Module',
                        validators=[
                            Optional(),
                            AnyOf(cards.keys(), message="Module not recognized.")
                        ])
    qty = StringField(label='Qty',
                      validators=[])

    def validate_qty(form, field):
        if form.ident.data:
            try:
                qty = int(field.data.strip())
                if qty <= 0:
                    raise ValidationError("Invalid Qty.")
            except:
                raise ValidationError("Invalid Qty.")
        else:
            if field.data:
                raise ValidationError("Detached Qty.")


class DeltaOrderForm(Form):
    orig_cardname = StringField(label='Original',
                                validators=[])
    target_cardname = StringField(label='Target',
                                  validators=[])
    sno = StringField(label='Serial Number',
                      validators=[])

    def validate_orig_cardname(form, field):
        cardname = field.data.strip()
        if form.sno.data and not cardname:
            raise ValidationError("Specify original Indent.")
        if form.target_cardname.data and not cardname:
            raise ValidationError("Specify original Indent.")
        if not cardname:
            return
        if cardname:
            if cardname not in cards.keys():
                raise ValidationError("Ident not recognized.")
        try:
            efield = serialnos.get_serialno_efield(sno=form.sno.data.strip())
            if cardname != efield:
                raise ValidationError("S.No. seems to be {0}.".format(efield))
        except SerialNoNotFound:
            pass

    def validate_target_cardname(form, field):
        cardname = field.data.strip()
        if form.sno.data and not cardname:
            raise ValidationError("Specify target Indent.")
        if form.orig_cardname.data and not cardname:
            raise ValidationError("Specify target Indent.")
        if not cardname:
            return
        if cardname not in cards.keys():
            raise ValidationError("Ident not recognized.")
        if form.orig_cardname.data.strip() == cardname:
            raise ValidationError("No change?")

    def validate_sno(form, field):
        sno = field.data.strip()
        if form.orig_cardname.data and not sno:
            raise ValidationError("Specify Serial No.")
        if form.target_cardname.data and not sno:
            raise ValidationError("Specify Serial No.")
        if not sno:
            return
        if not serialnos.serialno_exists(sno=sno):
            raise ValidationError("S.No. not recognized.")


class CreateProductionOrderForm(Form):
    user = StringField(label='Ordered By',
                       validators=[InputRequired(), user_auth_check])
    rdate = DateInputField(label='Date')
    prod_order_title = StringField(
            label='Title',
            validators=[InputRequired(), Length(max=50)]
    )
    desc = StringField(label='Description',
                       validators=[InputRequired()])
    root_order_sno = StringField(
        label='Root Order',
        validators=[Optional()]
    )
    prod_order_sno = FormField(NewSerialNumberForm)

    production_type = SelectField(
            label='Type', validators=[InputRequired()],
            choices=[("production", "Production"),
                     ("prototype", "Prototype"),
                     ("testing", "Testing"),
                     ("support", "Support"),
                     ("rd", "Research & Development")],
    )

    modules = FieldList(FormField(ModuleQtyForm), min_entries=1)
    deltas = FieldList(FormField(DeltaOrderForm), min_entries=1)

    def __init__(self, auth_roles=None, admin_roles=None, *args, **kwargs):
        if auth_roles is not None:
            self.auth_roles = auth_roles
        else:
            self.auth_roles = ['exec']
        if admin_roles is not None:
            self.admin_roles = admin_roles
        else:
            self.admin_roles = ['inventory_admin']
        super(CreateProductionOrderForm, self).__init__(*args, **kwargs)
        self._setup_sno_fields()
        self._setup_secure_fields()

    def _setup_sno_fields(self):
        sno_validator = self.prod_order_sno.sno.validators[0]
        sno_validator.series = 'PROD'
        sno_validator.new = True
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.prod_order_sno.sno_generate)
        read_only(self.prod_order_sno.sno)

    def _setup_secure_fields(self):
        if not self.user.data:
            self.user.data = current_user.full_name
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.user)
            read_only(self.rdate)
