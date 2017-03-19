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

# TODO Seriously refactor this file

from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import ident_transform
from tendril.conventions.electronics import DEVICE_CLASSES

from colorama import Fore
from colorama import Style
from tendril.utils import terminal
from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class ValidatableBase(object):
    def __init__(self):
        self._validated = False
        self._validation_context = None
        self._validation_errors = ErrorCollector()

    @property
    def ident(self):
        raise NotImplementedError

    @ident.setter
    def ident(self, value):
        raise NotImplementedError

    def _validate(self):
        raise NotImplementedError

    def validate(self):
        if not self._validated:
            logger.debug("Validating {0}".format(self.ident))
            self._validate()

    @property
    def validation_errors(self):
        if not self._validated:
            self._validate()
        return self._validation_errors


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
        self.detail = None

    @property
    def policy(self):
        return self._policy

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': self._policy.context.render(),
            'detail': self.detail,
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
                         "".format(', '.join(self._policy.options))
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
            option_str = "Valid options are {0}".format(', '.join(self._policy.options))
        else:
            option_str = ''
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' Invalid for {1} in {2}"
                        "".format(self._value, self._format_path(),
                                  self._policy.context.render()),
            'detail': "The value provided for this configuration option is "
                      "unrecognized or not allowed in this context. " + option_str,
        }


class IdentErrorBase(ValidationError):
    def __init__(self, policy, ident, refdeslist):
        self.ident = ident
        self.refdeslist = refdeslist
        self._policy = policy


class IdentNotRecognized(IdentErrorBase):
    msg = "Ident Not Recognized"

    def __init__(self, policy, ident, refdeslist):
        super(IdentNotRecognized, self).__init__(policy, ident, refdeslist)

    def __repr__(self):
        return "<IdentNotRecognized {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}'".format(self.ident),
            'detail': "This ident is not recognized by the library and is "
                      "therefore deemed invalid. Used by refdes {0}"
                      "".format(', '.join(self.refdeslist)),
            'detail_core': ', '.join(self.refdeslist),
        }


class DeviceNotRecognized(IdentErrorBase):
    msg = "Device Not Recognized"

    def __init__(self, policy, ident, refdeslist):
        super(DeviceNotRecognized, self).__init__(policy, ident, refdeslist)

    def __repr__(self):
        return "<DeviceNotRecognized {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' does not have a recognized Device."
                        "".format(self.ident),
            'detail': "This ident does not have a recognized device "
                      "string. It is therefore unlikely to be correctly "
                      "handled. Used by refdes {0}"
                      "".format(', '.join(self.refdeslist)),
        }


class QuantityTypeError(IdentErrorBase):
    msg = "Quantity Type Mismatch"

    def __init__(self, policy, ident, refdeslist):
        super(QuantityTypeError, self).__init__(policy, ident, refdeslist)

    def __repr__(self):
        return "<QuantityTypeError {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Quantity for '{0}' could not be determined."
                        "".format(self.ident),
            'detail': "The quantity for this ident could not be determined. "
                      "This is often due to mismatches / errors in the types "
                      "for one or more of the specified quantities. See {0}."
                      "".format(', '.join(self.refdeslist)),
        }


class BomGroupError(ValidationError):
    msg = "Group not found in Configs file"

    def __init__(self, policy, tgroup, refdes, ident=None):
        super(BomGroupError, self).__init__(policy)
        self._tgroup = tgroup
        self._refdes = refdes
        self._ident = ident

    def __repr__(self):
        return '<BomGroupError {0} {1}>'.format(self._tgroup, self._refdes)

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "Group '{0}' for {1} not found in the configs file."
                        "".format(self._tgroup, self._refdes),
            'detail': "The declared group should either be added to the "
                      "configs file, or changed to one of the defined "
                      "component groups - {0}."
                      "".format(', '.join(self.policy.known_groups)),
        }


class BomMotifUnrecognizedError(ValidationError):
    msg = "Motif Definition Unrecognized"

    def __init__(self, policy, motifst, refdes):
        super(BomMotifUnrecognizedError, self).__init__(policy)
        self._motifst = motifst
        self._refdes = refdes

    def __repr__(self):
        return '<BomMotifUnrecognizedError {0} {1}>' \
               ''.format(self._policy.context.render, self._motifst)

    def render(self):
        return {
            'group': self.msg,
            'is_error': self.policy.is_error,
            'headline': "Motif '{0}' for {1} is not recognized."
                        "".format(self._motifst, self._refdes),
            'detail': "The listed motif is not recognized by tendril and is "
                      "not handled. Component {0} is not included in the BOM."
                      "".format(self._refdes),
        }


class ConfigMotifMissingError(ValidationError):
    msg = "Motif in Configs not found in Schematic"

    def __init__(self, policy, refdes):
        super(ConfigMotifMissingError, self).__init__(policy)
        self.refdes = refdes

    def __repr__(self):
        return "<ConfigMotifMissingError {0} {1}>" \
               "".format(self.policy.context.render, self.refdes)

    def render(self):
        return {
            'group': self.msg,
            'is_error': self.policy.is_error,
            'headline': "Motif '{0}' could not be found in the schematic."
                        "".format(self.refdes),
            'detail': "No elements corresponding to motif {0} were found in "
                      "the schematic. None of the transformations related to "
                      "this motif configuration will be made to the BOM."
                      "".format(self.refdes),
        }


class ConfigGroupError(ValidationError):
    msg = "Group in config definitions unrecognized"

    def __init__(self, policy, groupname):
        super(ConfigGroupError, self).__init__(policy)
        self.groupname = groupname

    def __repr__(self):
        return "<ConfigGroupError {0}>".format(self.groupname)

    def render(self):
        return {
            'group': self.msg,
            'is_error': self.policy.is_error,
            'headline': "Group '{0}' unrecognized."
                        "".format(self.groupname),
            'detail': "This group is listed for inclusion in this "
                      "configuration but is not recognized. Recheck "
                      "configuration grouplist. Defined groups are : {0}."
                      "".format(', '.join(self.policy.known_groups)),
        }


class ConfigSJUnexpectedError(ValidationError):
    msg = "Fillstatus of non-configurable component changed"

    def __init__(self, policy, refdes, fillstatus):
        super(ConfigSJUnexpectedError, self).__init__(policy)
        self.refdes = refdes
        self.fillstatus = fillstatus

    def __repr__(self):
        return "<ConfigSJUnexpectedError {0} {1}>" \
               "".format(self.refdes, self.fillstatus)

    def render(self):
        return {
            'group': self.msg,
            'is_error': self.policy.is_error,
            'headline': "Unexpected inclusion of '{0}' with fillstatus '{1}' "
                        "in sjlist.".format(self.refdes, self.fillstatus),
            'detail': "This component's fillstatus is not expected to be "
                      "changed by the configs via the sjlist route. If "
                      "such modification is intended, change it's fillstatus "
                      "in the schematic to 'CONF'.",
        }


class ValidationPolicy(object):
    def __init__(self, context, is_error=True):
        self.context = context
        self.is_error = is_error


class ConfigMotifPolicy(ValidationPolicy):
    def __init__(self, context):
        super(ConfigMotifPolicy, self).__init__(context)
        self.is_error = True


class ConfigGroupPolicy(ValidationPolicy):
    def __init__(self, context, known_groups):
        super(ConfigGroupPolicy, self).__init__(context)
        self.is_error = True
        self.known_groups = known_groups


class ConfigSJPolicy(ValidationPolicy):
    def __init__(self, context):
        super(ConfigSJPolicy, self).__init__(context)
        self.is_error = False


class BomMotifPolicy(ValidationPolicy):
    def __init__(self, context):
        super(BomMotifPolicy, self).__init__(context)
        self.is_error = True


class BomGroupPolicy(ValidationPolicy):
    def __init__(self, context, known_groups, file_groups=None,
                 allow_blank=True, default='default'):
        super(BomGroupPolicy, self).__init__(context)
        self._known_groups = known_groups
        self._file_groups = file_groups
        self._allow_blank = allow_blank
        self._default = default
        self.is_error = False

    def check(self, item):
        group = item.data['group']
        schfile = item.data['schfile']
        if not schfile or schfile == 'unknown':
            schfiles = []
        else:
            schfiles = schfile.split(';')
        done = False
        if not group or group == 'unknown':
            for f in schfiles:
                if f in self.file_groups.keys():
                    group = self.file_groups[f]
                    done = True
            if not done:
                group = 'default'
        if group not in self._known_groups:
            raise BomGroupError(self, group,
                                item.data['refdes'],
                                ident_transform(item.data['device'],
                                                item.data['value'],
                                                item.data['footprint'])
                                )
        return group

    @property
    def default(self):
        return self._default

    @property
    def known_groups(self):
        return self._known_groups

    @property
    def file_groups(self):
        return self._file_groups


class IdentPolicy(ValidationPolicy):
    def __init__(self, context, rfunc):
        super(IdentPolicy, self).__init__(context)
        self.is_error = False
        self._rfunc = rfunc

    def check(self, ident, refdeslist, cstatus):
        d, v, f = parse_ident(ident)
        if d not in DEVICE_CLASSES:
            self.is_error = True
            raise DeviceNotRecognized(self, ident, refdeslist)
        if not self._rfunc(ident):
            self.is_error = False
            raise IdentNotRecognized(self, ident, refdeslist)


class IdentQtyPolicy(ValidationPolicy):
    def __init__(self, context, is_error):
        super(IdentQtyPolicy, self).__init__(context)
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
                if key not in d.keys():
                    raise KeyError
                d = d.get(key)
        except KeyError:
            raise ConfigKeyError(policy=policy)
        rval = d
    else:
        try:
            if policy.path not in d.keys():
                raise KeyError
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
                self._errors.append(error)
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

    def __repr__(self):
        rval = 'Collected Errors:\n'
        for e in self._errors:
            rval += '  {0}\n'.format(repr(e))
        return rval

    def _render_cli_group(self, g):
        for idx, i in enumerate(g):
            if 'detail_core' in i.keys():
                detail = i['detail_core']
            else:
                detail = i['detail']
            print("{0}.{1} : {2}"
                  "".format(idx + 1, i['headline'], detail))

    def render_cli(self, name):
        width = terminal.get_terminal_width()
        hline = '-' * width
        print(hline + Style.BRIGHT)
        titleformat = "{0:<" + str(width - 13) + "} {1:>2} {2}"
        print(titleformat.format(name, self.terrors, 'ALERTS') + Style.NORMAL)
        if self.nerrors:
            print(Fore.RED + hline)
            print(titleformat.format('', self.nerrors, 'ERRORS'))
            for n, g in self.errors_by_type.items():
                print(hline + Style.BRIGHT)
                print(titleformat.format(n, len(g), 'INSTANCES') + Style.NORMAL)
                self._render_cli_group(g)
        if self.nwarnings:
            print(Fore.YELLOW + hline)
            print(titleformat.format('', self.nwarnings, 'WARNINGS'))
            for n, g in self.warnings_by_type.items():
                print(hline + Style.BRIGHT)
                print(titleformat.format(n, len(g), 'INSTANCES') + Style.NORMAL)
                self._render_cli_group(g)
        print(Fore.RESET + Style.BRIGHT + hline + Style.NORMAL)
