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
Docstring for forms
"""
from decimal import Decimal

from flask_wtf import Form
from wtforms import StringField
from wtforms import BooleanField

from wtforms.validators import Optional
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError

from tendril.frontend.parts.forms import MultiCheckboxField

# TODO change reference to directory
from tendril.gedaif.gsymlib import gsymlib_idents
from tendril.conventions.electronics import fpiswire_ident
from tendril.utils.types import lengths
from tendril.sourcing.electronics import vendor_list


class SourcingIdentSearch(Form):
    ident = StringField(label='Ident', validators=[DataRequired()])
    qty = StringField(label='Quantity', validators=[Optional()])
    get_all = BooleanField(label='All Sourceable Candidates', default=False)
    allow_urident = BooleanField(label='Allow Arbitrary Idents',
                                 default=False)
    vendors = MultiCheckboxField(
        label='Vendors',
        choices=[(x._name, x._name) for x in vendor_list],
        default=[x._name for x in vendor_list]
    )

    def validate_ident(form, field):
        if form.allow_urident.data is False:
            if field.data.strip() in gsymlib_idents:
                return
        else:
            return
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
