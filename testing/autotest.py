"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


autotests = {}


def register_autotest(ident, testsuite):
    if ident not in autotests.keys():
        autotests[ident] = []
    autotests[ident].append(testsuite)
