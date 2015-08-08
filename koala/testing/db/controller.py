#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of koala.
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
Docstring for controller.py
"""

from koala.utils.db import with_db

from model import TestResult
from model import TestSuiteResult

from koala.entityhub import serialnos


@with_db
def create_test_model_obj(testobj=None, suite=None, session=None):
    if testobj.passed is True:
        passed = True
    else:
        passed = False
    tro = TestResult(test_class=repr(testobj.__class__),
                     passed=passed,
                     result=testobj.render())
    tro.testsuite = suite

    session.add(tro)
    return tro


@with_db
def commit_test_suite(suiteobj=None, session=None):
    sno = serialnos.get_serialno_object(sno=suiteobj.serialno, session=session)
    passed = suiteobj.passed

    sro = TestSuiteResult(suite_class=repr(suiteobj.__class__),
                          passed=passed)
    sro.serialno = sno

    session.add(sro)
    for test in suiteobj.tests:
        sro.tests.append(create_test_model_obj(testobj=test, suite=sro, session=session))
