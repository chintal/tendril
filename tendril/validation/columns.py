#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016-2019 Chintalagiri Shashank
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


from tendril.validation.base import ValidationError
from tendril.validation.base import ValidationPolicy


class RequiredColumnMissingError(ValidationError):
    msg = "Required Column Missing"

    def __init__(self, policy, missing_column):
        super(RequiredColumnMissingError, self).__init__(policy)
        self._missing_column = missing_column

    def __repr__(self):
        return "<Required Column Missing {0} {1}>".format(
            self._policy.context, self._missing_column
        )

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Required Column Missing",
            'detail': "{0}, Required Columns {1}"
                      "".format(self._policy.context.render(),
                                self._policy.required_columns),
        }


class ColumnsRequiredPolicy(ValidationPolicy):
    def __init__(self, context, required_columns):
        super(ColumnsRequiredPolicy, self).__init__(context)
        self.is_error = False
        self._required_columns = required_columns

    @property
    def required_columns(self):
        return self._required_columns

    def check(self, columns):
        for cname in self._required_columns:
            if cname not in columns:
                raise RequiredColumnMissingError(self, cname)
