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

from wtforms import Form
from wtforms.fields import StringField
from wtforms.validators import ValidationError

from flask_user import current_user
from tendril.frontend.users.controller import get_users_list


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
        else:
            self.data = arrow.utcnow()
