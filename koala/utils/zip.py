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
import zipfile


def zipdir(path, zfpath):
    zfile = zipfile.ZipFile(zfpath, 'w')
    for root, dirs, files in os.walk(path):
        for f in files:
            zfile.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.join(path, '..')))
    zfile.close()
    return zfpath
