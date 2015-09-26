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


import sys
import copy
import os
import arrow

from collections import namedtuple

from tendril.entityhub import serialnos
from tendril.entityhub import projects
from tendril.entityhub import macs
from tendril.entityhub.products import get_product_calibformat

from tendril.gedaif.conffile import ConfigsFile
from tendril.gedaif.conffile import NoGedaProjectException
from tendril.boms.electronics import import_pcb

from tendril.utils.fsutils import import_
from tendril.utils.config import INSTANCE_ROOT
from tendril.utils.config import PRINTER_NAME
from tendril.dox.docstore import register_document

from testbase import TestSuiteBase
from testbase import TestPrepUser
from tests import get_test_object
from db import controller

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


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
    logger.info("Adding Test Obj : " + repr(testobj))
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
                channeldefs.extend(
                    [ChannelDef(idx=k, name=v) for k, v in c.iteritems()]
                )
    return channeldefs


def replace_in_string(cnf_string, token, value, channelmap=None):
    if not isinstance(cnf_string, str):
        return cnf_string

    if channelmap is not None:
        mapped_strings = channelmap.keys()
    else:
        mapped_strings = None

    lidx = value
    if mapped_strings is not None:
        for s in mapped_strings:
            if cnf_string.startswith(s):
                lidx = channelmap[s][value]
                logger.debug("Applying channel map : " +
                             ' '.join([str(s), str(value), str(lidx)])
                             )

    return cnf_string.replace(token, str(lidx))


def replace_in_test_cnf_list(cnf_list, token, value, channelmap=None):
    l = copy.deepcopy(cnf_list)
    for idx, startval in enumerate(l):
        if isinstance(startval, str):
            l[idx] = replace_in_string(
                startval, token, value, channelmap
            )
        elif isinstance(startval, dict):
            l[idx] = replace_in_test_cnf_dict(
                startval, token, value, channelmap
            )
        elif isinstance(startval, list):
            l[idx] = replace_in_test_cnf_list(
                startval, token, value, channelmap
            )
    return l


def replace_in_test_cnf_dict(cnf_dict, token, value, channelmap=None):
    d = copy.deepcopy(cnf_dict)
    for key in d.keys():
        startval = d[key]
        if isinstance(startval, str):
            d[key] = replace_in_string(
                startval, token, value, channelmap
            )
        elif isinstance(startval, dict):
            d[key] = replace_in_test_cnf_dict(
                startval, token, value, channelmap
            )
        elif isinstance(startval, list):
            d[key] = replace_in_test_cnf_list(
                startval, token, value, channelmap
            )
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

    desc = None
    title = None
    if 'desc' in cnf_suite[cnf_suite.keys()[0]].keys():
        logger.debug("Found Test Suite Description")
        desc = cnf_suite[cnf_suite.keys()[0]]['desc']
    if 'title' in cnf_suite[cnf_suite.keys()[0]].keys():
        logger.debug("Found Test Suite Title")
        title = cnf_suite[cnf_suite.keys()[0]]['title']

    logger.debug("Creating test suite : " + cnf_suite_name)
    if cnf_suite_name == "TestSuiteBase":
        suite = []
        suite_detail = cnf_suite[cnf_suite_name]

        if 'group-tests' in suite_detail.keys():
            suite.append(TestSuiteBase())

            if 'prep' in suite_detail.keys():
                add_prep_steps_from_cnf_prep(suite[0], suite_detail['prep'])

            if desc is not None:
                suite[0].desc = desc
            if title is not None:
                suite[0].title = title

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
                        suite[0].add_test(
                            get_testobj_from_cnf_test(
                                cnf_test, testvars, bomobj, offline=offline
                            )
                        )

        if 'channel-tests' in suite_detail.keys():
            channel_defs = get_channel_defs_from_cnf_channels(
                suite_detail['channels'], cnf_grouplist
            )

            lsuites = []
            for channel_def in channel_defs:
                lsuite = TestSuiteBase()
                if 'prep' in suite_detail.keys():
                    add_prep_steps_from_cnf_prep(
                        lsuite,
                        replace_in_test_cnf_dict(
                            suite_detail['prep'], '<CH>', channel_def.idx
                        )
                    )
                if desc is not None:
                    lsuite.desc = replace_in_string(
                        desc, '<CH>', channel_def.idx
                    )
                if title is not None:
                    lsuite.title = replace_in_string(
                        title, '<CH>', channel_def.idx
                    )
                for test in suite_detail['channel-tests']:
                    if 'motif-map' in suite_detail.keys():
                        motifmap = suite_detail['motif-map']
                    else:
                        motifmap = None
                    cnf_test_dict = replace_in_test_cnf_dict(
                        test, '<CH>', channel_def.idx, motifmap
                    )
                    lsuite.add_test(
                        get_testobj_from_cnf_test(
                            cnf_test_dict, testvars, bomobj, offline=offline
                        )
                    )
                lsuites.append(lsuite)

            suite.extend(lsuites)
    else:
        suite = [get_test_object(cnf_suite)]

    return suite


def get_electronics_test_suites(serialno, devicetype, projectfolder,
                                offline=False):
    try:
        gcf = ConfigsFile(projectfolder)
        logger.info("Using gEDA configs file from : " +
                    projects.cards[devicetype])
    except NoGedaProjectException:
        raise AttributeError("gEDA project for " + devicetype + " not found.")
    cnf_suites = gcf.tests()
    for cnf_suite in cnf_suites:
        suite = get_suiteobj_from_cnf_suite(cnf_suite, gcf, devicetype,
                                            offline=offline)
        for lsuite in suite:
            lsuite.serialno = serialno
            logger.info("Constructed Suite : " + repr(lsuite))
            yield lsuite


def run_electronics_test(serialno, devicetype, projectfolder,
                         incremental=True):
    offline = False
    suites = []
    for suite in get_electronics_test_suites(serialno, devicetype,
                                             projectfolder, offline=offline):
        if offline is False:
            if incremental is True:
                latest = controller.get_latest_test_suite(
                    serialno=serialno,
                    suite_class=repr(suite.__class__),
                    descr=suite.desc
                )
                if latest and latest.passed and \
                        latest.created_at.floor('day') == \
                        arrow.utcnow().floor('day'):
                    suite_needs_be_run = False
                    suite.destroy()
                else:
                    suite_needs_be_run = True
            else:
                suite_needs_be_run = True
            if suite_needs_be_run is True:
                suite.run_test()
                commit_test_results(suite)
                suite.finish()
        suites.append(suite)
    return suites


def commit_test_results(suite):
    controller.commit_test_suite(suiteobj=suite)


def write_to_device(serialno, devicetype):
    try:
        modname = get_product_calibformat(devicetype)
        mod = import_(os.path.join(INSTANCE_ROOT, 'products',
                                   'calibformats', modname))
        func = getattr(mod, 'write_to_device')
        func(serialno, devicetype)
    except ImportError:
        logger.error("Write to device not implemented for devicetype : " +
                     devicetype)


def publish_and_print(serialno, devicetype, print_to_paper=False):
    from tendril.dox import testing
    pdfpath = testing.render_test_report(serialno=serialno)
    register_document(serialno=serialno, docpath=pdfpath,
                      doctype='TEST-RESULT', efield=devicetype,
                      series='TEST/' + serialnos.get_series(sno=serialno))
    if PRINTER_NAME and print_to_paper:
        os.system('lp -d {1} -o media=a4 {0}'.format(pdfpath, PRINTER_NAME))


def run_test(serialno=None):
    if serialno is None:
        raise AttributeError("serialno cannot be None")
    logger.info("Staring Test for Serial No : " + serialno)

    devicetype = serialnos.get_serialno_efield(sno=serialno)
    logger.info(serialno + " is device : " + devicetype)

    try:
        projectfolder = projects.cards[devicetype]
    except KeyError:
        raise AttributeError("Project for " + devicetype + " not found.")

    suites = run_electronics_test(serialno, devicetype, projectfolder)

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
