# Copyright (C) 2015-2019 Chintalagiri Shashank
#
# This file is part of Tendril.
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


from tendril.validation.base import ValidationPolicy
from tendril.validation.idents import IdentErrorBase


class SourcingIdentPolicy(ValidationPolicy):
    def __init__(self, context):
        super(SourcingIdentPolicy, self).__init__(context)
        self.is_error = True


class SourcingIdentNotRecognized(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotRecognized, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotRecognized {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}' is not a recognized component."
                        "".format(self.ident),
            'detail': "This component is not recognized by the library and "
                      "is therefore not sourceable. Component not included "
                      "in costing analysis. Used by refdes {0}"
                      "".format(', '.join(self.refdeslist)),
        }


class SourcingIdentNotSourceable(IdentErrorBase):
    msg = "Component Not Sourceable"

    def __init__(self, policy, ident, refdeslist):
        super(SourcingIdentNotSourceable, self).__init__(policy, ident,
                                                         refdeslist)

    def __repr__(self):
        return "<SourcingIdentNotSourceable {0} {1}>" \
               "".format(self.ident, ', '.join(self.refdeslist))

    def render(self):
        return {
            'is_error': self.policy.is_error,
            'group': self.msg,
            'headline': "'{0}'".format(self.ident),
            'detail': "Viable sources for this component are not known. "
                      "Component not included in costing analysis. Used by "
                      "refdes {0}".format(', '.join(self.refdeslist)),
            'detail_core': ', '.join(self.refdeslist)
        }
