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


from tendril.conventions.electronics import ident_transform

from tendril.validation.base import ValidationPolicy
from tendril.validation.base import ValidationError
from tendril.validation.idents import IdentErrorBase


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


class IdentQtyPolicy(ValidationPolicy):
    def __init__(self, context, is_error):
        super(IdentQtyPolicy, self).__init__(context)
        self.is_error = is_error


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


class ConfigGroupPolicy(ValidationPolicy):
    def __init__(self, context, known_groups):
        super(ConfigGroupPolicy, self).__init__(context)
        self.is_error = True
        self.known_groups = known_groups


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


class ConfigSJPolicy(ValidationPolicy):
    def __init__(self, context):
        super(ConfigSJPolicy, self).__init__(context)
        self.is_error = False
