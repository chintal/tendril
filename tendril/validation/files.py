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


class MissingFileError(ValidationError):
    msg = "Missing File"

    def __init__(self, policy):
        super(MissingFileError, self).__init__(policy)

    def __repr__(self):
        return "<MissingFileWarning {0} {1}>".format(
            self._policy.context, self._policy.path
        )

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Missing {0}".format(self._policy.context.render()),
            'detail': self._policy.path,
        }


class MangledFileError(ValidationError):
    msg = "Unable to Parse File"

    def __init__(self, policy):
        super(MangledFileError, self).__init__(policy)

    def __repr__(self):
        return "<MangledFileError {0} {1}>".format(
            self._policy.context, self._policy.path
        )

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Mangled {0}".format(self._policy.context.render()),
            'detail': self._policy.path,
        }


class FilePolicy(ValidationPolicy):
    def __init__(self, context, path, is_error):
        super(FilePolicy, self).__init__(context, is_error)
        self.path = path
