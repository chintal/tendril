# Copyright (C) 2015 Chintalagiri Shashank
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
"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

import os

from tendril.utils.config import TENDRIL_ROOT
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.fsutils import import_

INSTANCE_MOTIFS_ROOT = os.path.join(INSTANCE_ROOT, 'motifs')
INSTANCE_MOTIFS = import_(INSTANCE_MOTIFS_ROOT)


def create_motif_object(motifst):
    try:
        return INSTANCE_MOTIFS.create_motif_object(motifst)
    except ValueError:
        pass

    modname = motifst.split('.')[0]
    modstr = 'tendril.conventions.motifs.' + modname
    clsname = 'Motif' + modname

    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls(motifst)
        return instance
    except (ImportError, AttributeError):
        raise ValueError("Motif Unrecognized :" + motifst)

motifs_list = None


def get_motifs_list():
    motifs = INSTANCE_MOTIFS.get_motifs_list()
    motifspath = os.path.join(TENDRIL_ROOT, 'conventions', 'motifs')
    candidates = [f for f in os.listdir(motifspath)
                  if os.path.isfile(os.path.join(motifspath, f))
                  and not f.startswith('_')]
    for candidate in candidates:
        name, ext = os.path.splitext(candidate)
        if name in motifs:
            continue
        if ext == '.py':
            try:
                create_motif_object(name + '.1')
                motifs.append(name)
            except ValueError:
                pass

    return motifs
