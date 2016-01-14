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
from wtforms.validators import ValidationError

from wtforms_components import read_only

from flask_user import current_user

from tendril.frontend.parts.forms import DateInputField
from tendril.frontend.parts.forms import user_auth_check

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
                float(field.data.strip())
                raise ValidationError("Include Units")
            except ValidationError:
                raise
            except:
                pass
            try:
                lengths.Length(field.data.strip())
            except:
                raise ValidationError("Invalid Length")
        else:
            try:
                int(field.data.strip())
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
        validators=[AnyOf(dxproduction.get_all_prodution_order_snos_strings(),
                          message="Not a valid Production Order.")]
    )
    root_order_sno = StringField(
        label='Root Order',
        validators=[]
    )
    parent_indent_sno = StringField(
        label='Parent Indent',
        validators=[AnyOf(dxindent.get_all_indent_sno_strings(),
                          message="Not a valid Indent")]
    )
    indent_sno = StringField(
        label='Serial Number',
        validators=[]
    )
    indent_desc = StringField(label='Indent For',
                              validators=[InputRequired()])
    indent_type = SelectField(
            label='Type', validators=[InputRequired()],
            choices=[("production", "Production"),
                     ("testing", "Testing"),
                     ("support", "Support"),
                     ("rd", "Research & Development")],
    )

    sno_generate = BooleanField(label="Auto Generate")

    components = FieldList(FormField(ComponentQtyForm), min_entries=1)

    def __init__(self, auth_roles=None, admin_roles=None,
                 parent_indent_sno=None, *args, **kwargs):
        self.auth_roles = auth_roles
        if admin_roles is not None:
            self.admin_roles = admin_roles
        else:
            self.admin_roles = ['inventory_admin']
        self.parent_indent_sno_str = dxindent.get_root_indent_sno(
                serialno=parent_indent_sno)
        super(CreateIndentForm, self).__init__(*args, **kwargs)
        self._setup_secure_fields()
        self._setup_for_supplementary()

    def _setup_secure_fields(self):
        if not self.user.data:
            self.user.data = current_user.full_name
        if not current_user.has_roles(tuple(self.admin_roles)):
            read_only(self.user)
            read_only(self.rdate)
            read_only(self.sno_generate)

    def _setup_for_supplementary(self):
        if self.parent_indent_sno_str is None:
            self.is_supplementary = False
        else:
            self.is_supplementary = True

            prod_ord_sno_str = dxindent.get_indent_production_order(
                    serialno=self.parent_indent_sno_str)
            root_ord_sno_str = dxproduction.get_root_order(
                    serialno=prod_ord_sno_str)
            serialno_str = dxindent.get_new_supplementary_indent_sno(
                    serialno=self.parent_indent_sno_str)
            parent_indent_title = dxproduction.get_order_title(
                    serialno=prod_ord_sno_str)

            self.indent_title.data = "Supplement to " + self.parent_indent_sno_str

            if not self.prod_order_sno.data:
                self.prod_order_sno.data = prod_ord_sno_str
            read_only(self.prod_order_sno)

            if not self.root_order_sno.data:
                self.root_order_sno.data = root_ord_sno_str
            read_only(self.root_order_sno)

            if not self.parent_indent_sno.data:
                self.parent_indent_sno.data = self.parent_indent_sno_str

            if not self.indent_sno.data:
                self.indent_sno.data = serialno_str

        read_only(self.parent_indent_sno)
        read_only(self.indent_sno)
