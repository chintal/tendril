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

INSTANCE_INSTRUMENTS_ROOT = os.path.join(INSTANCE_ROOT, 'instruments')
INSTANCE_INSTRUMENTS = import_(INSTANCE_INSTRUMENTS_ROOT)


def get_instrument_object(instst):
    modname = instst
    modstr = 'koala.testing.instruments.' + modname
    clsname = 'Test' + instst
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
        raise ValueError("Test Unrecognized :" + instst)
