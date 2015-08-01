# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Koala.
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
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


import os

from koala.utils.config import INSTANCE_ROOT
from koala.utils.fs import import_


INSTANCE_INSTRUMENTS_ROOT = os.path.join(INSTANCE_ROOT, 'instruments')
INSTANCE_INSTRUMENTS = import_(INSTANCE_INSTRUMENTS_ROOT)


def get_instrument_object(instst):
    modname = instst
    modstr = 'koala.testing.instruments.' + modname
    clsname = 'Instrument' + instst
    try:
        return INSTANCE_INSTRUMENTS.get_test_object(instst)
    except ValueError:
        pass
    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls()
        return instance
    except ImportError:
        raise ValueError("Instrument Unrecognized :" + instst)
