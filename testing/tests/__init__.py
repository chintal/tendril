"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


def get_test_object(testst):
    modname = testst
    modstr = 'testing.tests.' + modname
    clsname = 'Test' + testst
    try:
        mod = __import__(modstr, fromlist=[clsname])
        cls = getattr(mod, clsname)
        instance = cls()
        return instance
    except ImportError:
        raise ValueError("Test Unrecognized :" + testst)
