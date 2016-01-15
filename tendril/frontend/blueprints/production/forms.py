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
from wtforms.validators import AnyOf
from wtforms.validators import Optional
from wtforms.validators import ValidationError

from wtforms_components import read_only

from flask_user import current_user

from tendril.frontend.parts.forms import DateInputField
from tendril.frontend.parts.forms import user_auth_check

from tendril.entityhub.projects import cards
# from tendril.inventory.electronics import get_recognized_repr


class ModuleQtyForm(Form):
    # TODO add customization field
    ident = StringField(label='Module',
                        validators=[
                            InputRequired(message="Blank rows aren't allowed")
                        ])
    qty = StringField(label='Qty',
                      validators=[InputRequired(message="Specify")])

    def validate_ident(form, field):
        if field.data.strip() in cards.keys():
            return
        # if field.data.strip() in get_recognized_repr():
        #     return
        raise ValidationError("Module not recognized")

    def validate_qty(form, field):
        try:
            int(field.data.strip())
        except:
            raise ValidationError("Invalid Qty")


class DeltaOrderForm(Form):
    orig_cardname = StringField(label='Original',
                                validators=[])
    target_cardname = StringField(label='Target',
                                  validators=[])
    sno = StringField(label='Serial Number',
                      validators=[])


class CreateProductionOrderForm(Form):
    user = StringField(label='Ordered By',
                       validators=[InputRequired(), user_auth_check])
    rdate = DateInputField(label='Date')
    prod_order_title = StringField(
            label='Title',
            validators=[InputRequired(), Length(max=50)]
    )
    root_order_sno = StringField(
        label='Root Order',
        validators=[Optional()]
    )
    prod_order_sno = StringField(
        label='Serial Number',
        validators=[]
    )
    production_type = SelectField(
            label='Type', validators=[InputRequired()],
            choices=[("production", "Production"),
                     ("prototype", "Prototype"),
                     ("testing", "Testing"),
                     ("support", "Support"),
                     ("rd", "Research & Development")],
    )

    sno_generate = BooleanField(label="Auto Generate")

    modules = FieldList(FormField(ModuleQtyForm), min_entries=1)
    deltas = FieldList(FormField(DeltaOrderForm), min_entries=1)

    def __init__(self, auth_roles=None, admin_roles=None, *args, **kwargs):
        self.auth_roles = auth_roles
        if admin_roles is not None:
            self.admin_roles = admin_roles
        else:
            self.admin_roles = ['inventory_admin']
        super(CreateProductionOrderForm, self).__init__(*args, **kwargs)
        self._setup_secure_fields()

    def _setup_secure_fields(self):
        if not self.user.data:
            self.user.data = current_user.full_name
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.user)
            read_only(self.rdate)
            read_only(self.sno_generate)
        read_only(self.prod_order_sno)
