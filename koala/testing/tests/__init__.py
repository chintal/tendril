"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import os
import imp

from koala.utils.config import INSTANCE_ROOT


def import_(filename):
    (path, name) = os.path.split(filename)
    (name, ext) = os.path.splitext(name)
    (f, filename, data) = imp.find_module(name, [path])
    return imp.load_module(name, f, filename, data)

INSTANCE_TESTS_ROOT = os.path.join(INSTANCE_ROOT, 'tests')
INSTANCE_TESTS = import_(INSTANCE_TESTS_ROOT)


def get_test_object(testst):
    modname = testst
    modstr = 'koala.testing.tests.' + modname
    clsname = 'Test' + testst
    try:
        return INSTANCE_TESTS.get_test_object(testst)
    except ValueError:
        pass
    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls()
        return instance
    except ImportError:
        raise ValueError("Test Unrecognized :" + testst)
