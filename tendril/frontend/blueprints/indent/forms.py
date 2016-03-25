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

from decimal import Decimal

from flask_wtf import Form
from wtforms.fields import StringField
from wtforms.fields import SelectField
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
from tendril.frontend.parts.forms import NewSerialNumberForm

from tendril.inventory.indent import InventoryIndent
from tendril.dox import indent as dxindent
from tendril.dox import production as dxproduction
from tendril.conventions.electronics import fpiswire_ident
from tendril.utils.types import lengths
from tendril.gedaif.gsymlib import gsymlib_idents
# from tendril.inventory.electronics import get_recognized_repr


class ComponentQtyForm(Form):
    ident = StringField(label='Component',
                        validators=[
                            InputRequired(message="Blank rows aren't allowed")
                        ]
                        )
    qty = StringField(label='Qty',
                      validators=[InputRequired(message="Specify")])

    def validate_ident(form, field):
        if field.data.strip() in gsymlib_idents:
            return
        # if field.data.strip() in get_recognized_repr():
        #     return
        raise ValidationError("Ident not recognized")

    def validate_qty(form, field):
        # TODO integrate this with inventory core?
        ident = str(form.ident.data.strip())
        if fpiswire_ident(ident):
            try:
                Decimal(field.data.strip())
                raise ValidationError("Include Units")
            except ValidationError:
                raise
            except:
                pass
            try:
                qty = lengths.Length(field.data.strip())
                if qty <= 0:
                    raise ValidationError("Invalid Length")
            except:
                raise ValidationError("Invalid Length")
        else:
            try:
                qty = int(field.data.strip())
                if qty <= 0:
                    raise ValidationError("Invalid Qty")
            except:
                raise ValidationError("Invalid Qty")


class CreateIndentForm(Form):
    user = StringField(label='Requested By',
                       validators=[InputRequired(), user_auth_check])
    rdate = DateInputField(label='Date')
    indent_title = StringField(label='Title',
                               validators=[InputRequired(), Length(max=50)])
    prod_order_sno = StringField(
        label='Production Order',
        validators=[Optional(),
                    AnyOf(dxproduction.get_all_prodution_order_snos_strings(),
                          message="Not a valid Production Order.")]
    )
    root_order_sno = StringField(
        label='Root Order',
        validators=[Optional()]
    )
    parent_indent_sno = StringField(
        label='Parent Indent',
        validators=[Optional(),
                    AnyOf(dxindent.get_all_indent_sno_strings(),
                          message="Not a valid Indent")]
    )
    indent_sno = FormField(NewSerialNumberForm)
    indent_desc = StringField(label='Indent For',
                              validators=[InputRequired()])
    indent_type = SelectField(
            label='Type', validators=[InputRequired()],
            choices=[("production", "Production"),
                     ("prototype", "Prototype"),
                     ("testing", "Testing"),
                     ("support", "Support"),
                     ("rd", "Research & Development")],
    )

    components = FieldList(FormField(ComponentQtyForm), min_entries=1)

    def __init__(self, auth_roles=None, admin_roles=None,
                 parent_indent_sno=None, *args, **kwargs):
        if auth_roles is not None:
            self.auth_roles = auth_roles
        else:
            self.auth_roles = ['exec']
        if admin_roles is not None:
            self.admin_roles = admin_roles
        else:
            self.admin_roles = ['inventory_admin']
        if parent_indent_sno is not None:
            parent_indent = InventoryIndent(parent_indent_sno)
            self.parent_indent_sno_str = parent_indent.root_indent_sno
        else:
            self.parent_indent_sno_str = None
        super(CreateIndentForm, self).__init__(*args, **kwargs)
        self._setup_secure_fields()
        self._setup_for_supplementary()
        self._setup_sno_fields()

    def _setup_sno_fields(self):
        sno_validator = self.indent_sno.sno.validators[0]
        sno_validator.series = 'IDT'
        sno_validator.new = True
        if self.is_supplementary:
            sno_validator.parent = self.parent_indent_sno_str
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.indent_sno.sno_generate)
            read_only(self.indent_sno.sno)

    def _setup_secure_fields(self):
        if not self.user.data:
            self.user.data = current_user.full_name
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.user)
            read_only(self.rdate)

    def _setup_for_supplementary(self):
        if self.parent_indent_sno_str is None:
            self.is_supplementary = False
        else:
            self.is_supplementary = True
            parent_indent = InventoryIndent(self.parent_indent_sno_str)
            prod_ord_sno_str = parent_indent.prod_order_sno
            if len(parent_indent.root_order_snos):
                root_ord_sno_str = parent_indent.root_order_snos[0]
            else:
                root_ord_sno_str = None

            parent_indent_title = parent_indent.title

            self.indent_title.data = "Supplement to " + \
                                     self.parent_indent_sno_str

            if not self.prod_order_sno.data:
                self.prod_order_sno.data = prod_ord_sno_str
            read_only(self.prod_order_sno)

            if not self.root_order_sno.data:
                self.root_order_sno.data = root_ord_sno_str
            read_only(self.root_order_sno)

            if not self.parent_indent_sno.data:
                self.parent_indent_sno.data = self.parent_indent_sno_str

        read_only(self.parent_indent_sno)

    def get_supplementary_sno_default(self):
        parent_indent = InventoryIndent(self.parent_indent_sno_str)
        sindents = parent_indent.supplementary_indent_snos
        if len(sindents):
            sidx = str(max([int(x.split('.')[1]) for x in sindents]) + 1)
        else:
            sidx = '1'
        serialno_str = '.'.join([self.parent_indent_sno_str, sidx])
        return serialno_str
