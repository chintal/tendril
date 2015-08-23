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


from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import sys
import copy
import os

from collections import namedtuple

from tendril.entityhub import serialnos
from tendril.entityhub import projects
from tendril.entityhub import macs
from tendril.entityhub.products import get_product_calibformat

from tendril.gedaif.conffile import ConfigsFile
from tendril.gedaif.conffile import NoGedaProjectException
from tendril.boms.electronics import import_pcb

from tendril.utils.fs import import_
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.config import PRINTER_NAME
from tendril.dox.docstore import register_document

from testbase import TestSuiteBase
from testbase import TestPrepUser

from tests import get_test_object

from db import controller


def add_prep_steps_from_cnf_prep(testobj, cnf_prep):
    for step in cnf_prep:
        if 'user' in step.keys():
            stepobj = TestPrepUser(step['user'])
            testobj.add_prep(stepobj)


def get_testobj_from_cnf_test(cnf_test, testvars, bomobj, offline=False):
    if len(cnf_test.keys()) != 1:
        raise ValueError("Test configurations are "
                         "expected to have exactly "
                         "one key at the top level")
    logger.debug("Creating test object : " + cnf_test.keys()[0])
    testobj = get_test_object(cnf_test.keys()[0], offline=offline)
    additionalvars = cnf_test[cnf_test.keys()[0]]
    if 'prep' in additionalvars.keys():
        add_prep_steps_from_cnf_prep(testobj, additionalvars.pop('prep'))
    vardict = copy.copy(testvars)
    if additionalvars is not None:
        vardict.update(additionalvars)
    logger.debug("Configuring test object : " + cnf_test.keys()[0])
    if 'desc' in vardict.keys():
        testobj.desc = vardict.pop('desc')
    if 'title' in vardict.keys():
        testobj.title = vardict.pop('title')
    testobj.use_bom(bomobj)
    testobj.configure(**vardict)
    logger.info("Adding test object to suite : " + repr(testobj))
    return testobj


ChannelDef = namedtuple('ChannelDef', ['idx', 'name'])


def get_channel_defs_from_cnf_channels(channeldict, grouplist):
    channeldefs = []
    for groupdict in channeldict:
        if len(groupdict.keys()) != 1:
            raise ValueError("Channel group configurations are expected "
                             "to have exactly one key at the top level")
        groupname = groupdict.keys()[0]
        if groupname in grouplist:
            channellist = groupdict[groupname]
            for c in channellist:
                channeldefs.extend([ChannelDef(idx=k, name=v) for k, v in c.iteritems()])
    return channeldefs


def replace_in_test_cnf_dict(cnf_dict, token, value):
    d = copy.deepcopy(cnf_dict)
    for key in d[d.keys()[0]].keys():
        try:
            d[d.keys()[0]][key] = d[d.keys()[0]][key].replace(token, str(value))
        except (TypeError, AttributeError):
            pass
    return d


def get_suiteobj_from_cnf_suite(cnf_suite, gcf, devicetype, offline=False):
    if len(cnf_suite.keys()) != 1:
        raise ValueError("Suite configurations are expected "
                         "to have exactly one key at the top level")
    cnf_suite_name = cnf_suite.keys()[0]
    testvars = gcf.testvars(devicetype)
    bomobj = import_pcb(gcf.projectfolder)
    bomobj.configure_motifs(devicetype)
    cnf_grouplist = gcf.config_grouplist(devicetype)
    logger.debug("Creating test suite : " + cnf_suite_name)
    if cnf_suite_name == "TestSuiteBase":
        suite = TestSuiteBase()
        suite_detail = cnf_suite[cnf_suite_name]
        if 'prep' in suite_detail.keys():
            add_prep_steps_from_cnf_prep(suite, suite_detail['prep'])
        if 'group-tests' in suite_detail.keys():
            cnf_groups = suite_detail['group-tests']
            for cnf_group in cnf_groups:
                if len(cnf_suite.keys()) != 1:
                    raise ValueError("Group test configurations are "
                                     "expected to have exactly one "
                                     "key at the top level")
                logger.debug("Creating group tests : " + cnf_group.keys()[0])
                if cnf_group.keys()[0] in cnf_grouplist:
                    cnf_test_list = cnf_group[cnf_group.keys()[0]]
                    for cnf_test in cnf_test_list:
                        suite.add_test(get_testobj_from_cnf_test(cnf_test,
                                                                 testvars,
                                                                 bomobj,
                                                                 offline=offline))
        if 'channel-tests' in suite_detail.keys():
            channel_defs = get_channel_defs_from_cnf_channels(suite_detail['channels'],
                                                              cnf_grouplist)
            for test in suite_detail['channel-tests']:
                for channel_def in channel_defs:
                    cnf_test_dict = replace_in_test_cnf_dict(test, '<CH>',
                                                             channel_def.idx)
                    suite.add_test(get_testobj_from_cnf_test(cnf_test_dict,
                                                             testvars, bomobj,
                                                             offline=offline))
    else:
        suite = get_test_object(cnf_suite)
    if 'desc' in cnf_suite.keys():
        suite.desc = cnf_suite['desc']
    if 'title' in cnf_suite.keys():
        suite.title = cnf_suite['title']
    return suite


def get_electronics_test_suites(serialno, devicetype, projectfolder, offline=False):
    try:
        gcf = ConfigsFile(projectfolder)
        logger.info("Using gEDA configs file from : " + projects.cards[devicetype])
    except NoGedaProjectException:
        raise AttributeError("gEDA project for " + devicetype + " not found.")
    suites = []
    cnf_suites = gcf.tests()
    for cnf_suite in cnf_suites:
        suite = get_suiteobj_from_cnf_suite(cnf_suite, gcf, devicetype, offline=offline)
        suite.serialno = serialno
        logger.info("Created test suite : " + repr(suite))
        suites.append(suite)
    return suites


def run_electronics_test(serialno, devicetype, projectfolder):
    suites = get_electronics_test_suites(serialno, devicetype, projectfolder)
    for suite in suites:
        suite.run_test()
    return suites


def commit_test_results(suites):
    for suite in suites:
        controller.commit_test_suite(suiteobj=suite)


def write_to_device(serialno, devicetype):
    try:
        modname = get_product_calibformat(devicetype)
        mod = import_(os.path.join(INSTANCE_ROOT, 'products', 'calibformats', modname))
        func = getattr(mod, 'write_to_device')
        func(serialno, devicetype)
    except ImportError:
        logger.error("Write to device not implemented for devicetype : "
                     + devicetype)


def publish_and_print(serialno, devicetype, print_to_paper=False):
    from tendril.dox import testing
    pdfpath = testing.render_test_report(serialno=serialno)
    register_document(serialno=serialno, docpath=pdfpath,
                      doctype='TEST-RESULT', efield=devicetype,
                      series='TEST/' + serialnos.get_series(sno=serialno))
    if print_to_paper:
        os.system('lp -d {1} -o media=a4 {0}'.format(pdfpath, PRINTER_NAME))


def run_test(serialno=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    logger.info("Staring test for serial no : " + serialno)

    devicetype = serialnos.get_serialno_efield(sno=serialno)
    logger.info(serialno + " is device : " + devicetype)

    try:
        projectfolder = projects.cards[devicetype]
    except KeyError:
        raise AttributeError("Project for " + devicetype + " not found.")

    suites = run_electronics_test(serialno, devicetype, projectfolder)

    user_input = raw_input("Discard Results [y/N] ?: ").strip()
    if user_input.lower() in ['y', 'yes', 'ok', 'pass']:
        return suites
    else:
        commit_test_results(suites)

    for suite in suites:
        suite.finish()

    user_input = raw_input("Write to device [y/N] ?: ").strip()
    if user_input.lower() in ['y', 'yes', 'ok', 'pass']:
        write_to_device(serialno, devicetype)

    user_input = raw_input("Print to Paper [y/N] ?: ").strip()
    if user_input.lower() in ['y', 'yes', 'ok', 'pass']:
        publish_and_print(serialno, devicetype, print_to_paper=True)
    else:
        publish_and_print(serialno, devicetype, print_to_paper=False)

    return suites


if __name__ == '__main__':
    if sys.argv[1] == 'detect':
        mactype = sys.argv[2]
        sno = macs.get_sno_from_device(mactype)
    else:
        sno = sys.argv[1]
    run_test(sno)
