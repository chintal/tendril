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

from tendril.frontend.app import app, db
from tendril.frontend.startup.init_app import init_app

import os
import atexit
from tendril.utils.config import INSTANCE_ROOT

from tendril.dox.docstore import instance_assets_fs


def mount():
    # mount exposed filesystems
    expose_path = os.path.join(INSTANCE_ROOT, 'mp_exposed')
    if not os.path.exists(expose_path):
        os.makedirs(expose_path)
        print "Mounting exposed filesystems", expose_path
        from fs.expose import fuse
        expose_mp = fuse.mount(instance_assets_fs, expose_path)
        atexit.register(unmount, expose_mp)
    else:
        # Assume the filesystem is already mounted. Don't
        # use this in any kind of production whatsoever.
        pass


def unmount(mp):
    mpath = mp.path
    print "Unmounting exposed filesystems", mpath
    mp.unmount()
    os.rmdir(mpath)


mount()
init_app(app, db)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
