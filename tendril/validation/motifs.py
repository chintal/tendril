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


class BomMotifPolicy(ValidationPolicy):
    def __init__(self, context):
        super(BomMotifPolicy, self).__init__(context)
        self.is_error = True


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


class ConfigMotifPolicy(ValidationPolicy):
    def __init__(self, context):
        super(ConfigMotifPolicy, self).__init__(context)
        self.is_error = True
