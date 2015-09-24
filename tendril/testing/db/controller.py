#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of tendril.
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

from tendril.utils.db import with_db

from model import TestResult
from model import TestSuiteResult

from tendril.entityhub import serialnos
from tendril.entityhub.db.model import SerialNumber

from sqlalchemy import desc


@with_db
def create_test_model_obj(testobj=None, suite=None, session=None):
    if testobj.passed is True:
        passed = True
    else:
        passed = False
    tro = TestResult(test_class=repr(testobj.__class__),
                     passed=passed,
                     result=testobj.render(),
                     desc=testobj.desc,
                     title=testobj.title)
    tro.testsuite = suite

    if testobj.ts is not None:
        tro.created_at = testobj.ts

    session.add(tro)
    return tro


@with_db
def commit_test_suite(suiteobj=None, session=None):
    sno = serialnos.get_serialno_object(sno=suiteobj.serialno,
                                        session=session)
    passed = suiteobj.passed

    sro = TestSuiteResult(suite_class=repr(suiteobj.__class__),
                          passed=passed,
                          desc=suiteobj.desc,
                          title=suiteobj.title)
    sro.serialno = sno

    if suiteobj.ts is not None:
        sro.created_at = suiteobj.ts

    session.add(sro)
    for test in suiteobj.tests:
        sro.tests.append(
            create_test_model_obj(testobj=test, suite=sro, session=session)
        )


@with_db
def get_test_suites(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)
    return session.query(
        TestSuiteResult).filter_by(serialno=serialno).order_by(
        desc(TestSuiteResult.created_at)).all()


@with_db
def get_latest_test_result(serialno=None, test_class=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if test_class is None:
        raise AttributeError("testclass cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)
    if not isinstance(test_class, str):
        test_class = repr(test_class.__class__)
    return session.query(TestResult).filter_by(
        test_class=test_class).join(
        TestSuiteResult).filter(
        TestSuiteResult.serialno == serialno).order_by(
        desc(TestResult.created_at)).first()


@with_db
def get_latest_test_suite(serialno=None, suite_class=None,
                          descr=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)
    q = session.query(TestSuiteResult).filter_by(
        serialno=serialno, suite_class=suite_class
    )
    if descr is not None:
        q = q.filter_by(desc=descr)
    q = q.order_by(desc(TestSuiteResult.created_at))
    return q.first()


@with_db
def get_test_suite_names(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)
    return [x[0] for x in
            session.query(
                TestSuiteResult.suite_class).filter_by(
                serialno=serialno).distinct().all()
            ]


@with_db
def get_test_suite_descs(serialno=None, session=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    if not isinstance(serialno, SerialNumber):
        serialno = serialnos.get_serialno_object(sno=serialno,
                                                 session=session)
    return session.query(
        TestSuiteResult.desc, TestSuiteResult.suite_class).filter_by(
        serialno=serialno).distinct().all()
