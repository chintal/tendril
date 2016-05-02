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
Docstring for validate
"""


class ValidationContext(object):
    def __init__(self, mod, locality=None):
        self.mod = mod
        self.locality = locality

    def __repr__(self):
        if self.locality:
            return '/'.join([self.mod, self.locality])
        else:
            return self.mod

    def render(self):
        return self.locality


class ValidationError(Exception):
    msg = "Validation Error"

    def __init__(self, policy):
        self._policy = policy

    @property
    def policy(self):
        return self._policy

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': self._policy.context.render(),
            'detail': None,
        }


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


class ContextualConfigError(ValidationError):
    msg = "Incorrect Configuration"

    def __init__(self, policy):
        super(ContextualConfigError, self).__init__(policy)

    def _format_path(self):
        if isinstance(self._policy.path, tuple):
            return '/'.join(self._policy.path)
        else:
            return self._policy.path

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': self._policy.context.render(),
            'detail': "Configuration seems to be incorrect.",
        }


class ConfigKeyError(ContextualConfigError):
    msg = "Configuration Key Missing"

    def __init__(self, policy):
        super(ConfigKeyError, self).__init__(policy)

    def __repr__(self):
        return "<ConfigKeyError {0} {1}>" \
               "".format(self._policy.context, self._format_path())

    def render(self):
        if self._policy.options:
            option_str = "Valid options are {0}" \
                         "".format(','.join(self._policy.options))
        else:
            option_str = ''
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "{0} missing in {1}"
                        "".format(self._format_path(),
                                  self._policy.context.render()),
            'detail': "This required configuration option could not be "
                      "found in the configs file. " + option_str,
        }


class ConfigValueInvalidError(ContextualConfigError):
    msg = "Configuration Value Unrecognized"

    def __init__(self, policy, value):
        super(ConfigValueInvalidError, self).__init__(policy)
        self._value = value

    def __repr__(self):
        return "<ConfigValueInvalidError {0} {1}>" \
               "".format(self._policy.context, self._format_path())

    def render(self):
        if self._policy.options:
            option_str = "Valid options are {0}".format(','.join(self._policy.options))
        else:
            option_str = ''
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Invalid {0} for {1} in {2}"
                        "".format(self._value, self._format_path(),
                                  self._policy.context.render()),
            'detail': "The value provided for this configuration option is "
                      "unrecognized or not allowed in this context. " + option_str,
        }


class ValidationPolicy(object):
    def __init__(self, context, is_error=True):
        self.context = context
        self.is_error = is_error


class ConfigOptionPolicy(ValidationPolicy):
    def __init__(self, context, path, options=None, default=None, is_error=True):
        super(ConfigOptionPolicy, self).__init__(context, is_error)
        self.path = path
        self.options = options
        self.default = default


class FilePolicy(ValidationPolicy):
    def __init__(self, context, path, is_error):
        super(FilePolicy, self).__init__(context, is_error)
        self.path = path


def get_dict_val(d, policy=None):
    assert isinstance(d, dict)
    if isinstance(policy.path, tuple):
        try:
            for key in policy.path:
                d = d.get(key)
        except KeyError:
            raise ConfigKeyError(policy=policy)
        rval = d
    else:
        try:
            rval = d.get(policy.path)
        except KeyError:
            raise ConfigKeyError(policy=policy)

    if policy.options is None or rval in policy.options:
        return rval
    else:
        raise ConfigValueInvalidError(policy=policy, value=rval)


class ErrorCollector(ValidationError):
    def __init__(self):
        self._errors = []

    def add(self, e):
        if isinstance(e, ErrorCollector):
            for error in e.errors:
                self.add(error)
        else:
            self._errors.append(e)

    @property
    def errors(self):
        return self._errors

    @property
    def terrors(self):
        return len(self._errors)

    @property
    def derrors(self):
        return [x for x in self._errors if x.policy.is_error]

    @property
    def dwarnings(self):
        return [x for x in self._errors if not x.policy.is_error]

    @property
    def nerrors(self):
        return len(self.derrors)

    @property
    def nwarnings(self):
        return len(self.dwarnings)

    @staticmethod
    def _group_errors(errors):
        rval = {}
        for error in errors:
            etype = error['group']
            if etype in rval.keys():
                rval[etype].append(error)
            else:
                rval[etype] = [error]
        return rval

    @property
    def errors_by_type(self):
        lerrors = [x.render() for x in self.derrors]
        return self._group_errors(lerrors)

    @property
    def warnings_by_type(self):
        lwarnings = [x.render() for x in self.dwarnings]
        return self._group_errors(lwarnings)
