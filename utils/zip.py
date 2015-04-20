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
