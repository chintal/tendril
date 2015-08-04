#!/usr/bin/env python
# encoding: utf-8

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
Docstring for migratesno
"""

from koala.utils import log
logger = log.get_logger(__name__, log.DEBUG)

from koala.entityhub import serialnos

from koala.entityhub.db.model import SerialNumber
from koala.entityhub.db.model import SerialNumberAssociation

from koala.utils import db


if __name__ == "__main__":
    with db.get_session() as s:
        serialdict = {}
        for sno in serialnos.get_all_serialnos():
            logger.debug('::'.join([str(sno['sno']), str(sno['id']), str(sno['efield']), str(sno['parent'])]))
            sobj = SerialNumber(sno=sno['sno'], efield=sno['efield'])
            s.add(sobj)
            s.flush()
            serialdict[sno['sno']] = sobj

        for sno in serialnos.get_all_serialnos():
            if sno['parent'] is not None:
                parent = serialdict[sno['parent']]
                child = serialdict[sno['sno']]
                assoc = SerialNumberAssociation(child_id=child.id, child=child, parent_id=parent.id, parent=parent, association_type="UNSET")
                s.add(assoc)
                s.flush()
