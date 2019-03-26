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


from tendril.conventions.electronics import parse_ident
from tendril.conventions.electronics import DEVICE_CLASSES

from tendril.validation.base import ValidationError
from tendril.validation.base import ValidationPolicy


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
