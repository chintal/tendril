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
Docstring for fields
"""

import arrow
from idstring import IDstring

from flask_wtf import Form
from wtforms.fields import StringField
from wtforms.fields import BooleanField
from wtforms.fields import SelectMultipleField
from wtforms import widgets
from wtforms.validators import ValidationError
from wtforms.validators import StopValidation

from flask_user import current_user
from tendril.auth.db.controller import get_users_list
from tendril.entityhub import serialnos
from tendril.dox import docstore


def user_auth_check(form, field):
    fuser = field.data
    if current_user.has_roles(tuple(form.admin_roles)):
        full_names = [x.full_name for x in get_users_list()]
        if fuser in full_names:
            return
        else:
            raise ValidationError("User '{0}' not recognized.".format(fuser))
    if fuser == current_user.full_name:
        if len(form.auth_roles):
            if current_user.has_roles(tuple(form.auth_roles)):
                return
            else:
                raise ValidationError("You are not authorized for this "
                                      "action.".format(fuser))
    raise ValidationError("You are not authorized to act on behalf on {0} for"
                          "this action".format(fuser))


class SerialNumberValidator(object):
    def __init__(self, new=True, series=None, efield=None,
                 has_doctype=None, parent=None, message=None):
        self.new = new
        self.series = series
        self.efield = efield
        self.has_doctype = has_doctype
        self.parent = parent
        if message is None:
            self._message = "Invalid Serial Number."
        else:
            self._message = message

    def _check_valid(self, sno):
        if not sno:
            raise ValidationError("Required, or select Autogenerate.")
        try:
            number = serialnos.get_number(sno).split('.')[0]
        except:
            raise ValidationError(self._message +
                                  " Malformed Format.")
        if not IDstring.sumcheck(number):
            raise ValidationError(self._message +
                                  " Bad Checksum.")

    def _check_new(self, sno):
        exists = serialnos.serialno_exists(sno=sno)
        if self.new is True and exists:
            raise ValidationError(self._message +
                                  " Already exists.")
        elif self.new is False and not exists:
            raise ValidationError(self._message +
                                  " Does not exist.")

    def _check_series(self, sno):
        series = serialnos.get_series(sno)
        if series == sno:
            raise ValidationError(self._message + " Malformed format.")
        if isinstance(self.series, str) and series != self.series:
            raise ValidationError(
                self._message +
                " Must be of '{0}' series.".format(self.series)
            )
        elif isinstance(self.series, list) and series not in self.series:
            raise ValidationError(
                self._message + "'{0}' Series not allowed.".format(series)
            )

    def _check_efield(self, sno):
        try:
            efield = serialnos.get_serialno_efield(sno=sno)
        except:
            raise ValidationError(self._message)
        if isinstance(self.efield, str) and efield != self.efield:
            raise ValidationError(
                self._message +
                " Efield must be '{0}'.".format(self.efield)
            )
        elif isinstance(self.efield, list) and efield not in self.efield:
            raise ValidationError(
                self._message + "'{0}' Efield not allowed.".format(efield)
            )

    def _check_has_doctype(self, sno):
        try:
            docs = docstore.get_docs_list_for_sno_doctype(
                    serialno=sno, doctype=self.has_doctype
            )
            if len(docs) == 0:
                raise ValidationError(
                    self._message +
                    " Doctype '{0}' not found.".format(self.has_doctype)
                )
        except:
            raise ValidationError(
                self._message +
                " Doctype '{0}' not found.".format(self.has_doctype)
            )

    def _check_parent(self, sno):
        if sno.split('.')[0] != self.parent:
            raise ValidationError(
                self._message + " Must derive from {0}.".format(self.parent)
            )

    def __call__(self, form, field):
        sno = field.data
        if form.sno_generate.data is True:
            if sno:
                raise ValidationError(
                        "To autogenerate, but Serial Number specified."
                )
            raise StopValidation
        self._check_valid(sno)
        self._check_new(sno)
        if self.parent is not None:
            self._check_parent(sno)
        if self.series is not None:
            self._check_series(sno)
        if self.efield is not None:
            self._check_efield(sno)
        if self.has_doctype is not None:
            self._check_has_doctype(sno)


class NewSerialNumberForm(Form):
    sno = StringField(
            label='Serial Number',
            validators=[SerialNumberValidator(new=True)]
    )

    sno_generate = BooleanField(label="Auto Generate")

    def __init__(self, **kwargs):
        super(NewSerialNumberForm, self).__init__(**kwargs)


class DateInputField(StringField):
    def __init__(self, label=None, validators=None,
                 date_format=None, **kwargs):
        if label is None:
            label = 'rdate'
        if date_format is not None:
            self.date_format = date_format
        else:
            self.date_format = 'DD/MM/YYYY'
        super(DateInputField, self).__init__(label, validators, **kwargs)

    def _value(self):
        if self.data:
            return self.data.format(self.date_format)
        else:
            return u''

    def process_formdata(self, valuelist):
        if str(valuelist[0]):
            self.data = arrow.get(valuelist[0].strip(), self.date_format)

    def get_date_default(self):
        return arrow.utcnow().isoformat()


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
