#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
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
Docstring for modules
"""

import os
import json
import timeit
from copy import copy
from copy import deepcopy

from future.utils import viewitems

from tendril.boms.electronics import EntityElnBom
from tendril.gedaif.conffile import ConfigsFile

from tendril.boms.validate import ConfigOptionPolicy
from tendril.boms.validate import ErrorCollector
from tendril.boms.validate import IdentPolicy
from tendril.boms.validate import IdentQtyPolicy
from tendril.boms.validate import QuantityTypeError
from tendril.boms.validate import ValidationContext
from tendril.boms.validate import ValidationError
from tendril.boms.validate import get_dict_val
from tendril.boms.costingbase import NoStructureHereException
from tendril.dox.gedaproject import get_docs_list
from tendril.utils.types import ParseException

from tendril.utils.connectors import mq
from tendril.utils.config import WARM_UP_CACHES
from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.config import SVN_ROOT

from . import projects
from . import serialnos
from .db.controller import SerialNoNotFound
from .entitybase import EntityBase
from .prototypebase import PrototypeBase

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


class ModuleNotRecognizedError(Exception):
    pass


class ModuleTypeError(Exception):
    pass


class ModuleInstanceTypeMismatchError(Exception):
    pass


class ModulePrototypeBase(PrototypeBase):
    prevalidator = None

    def __init__(self, modulename):
        super(ModulePrototypeBase, self).__init__()
        self._modulename = None
        self._configs = None
        self._bom = None
        self._obom = None
        self._status = None
        self._strategy = None
        self._changelog = None
        self._validated = False
        self._sourcing_errors = None
        self._indicative_cost = None
        self.ident = modulename
        self._register_for_changes()

    @property
    def ident(self):
        return self._modulename

    @ident.setter
    def ident(self, value):
        if value not in projects.cards.keys():
            raise ModuleNotRecognizedError(
                    "Module {0} not recognized".format(value))
        if not self.prevalidator(value):
            raise ModuleTypeError("Module {0} is not a not a valid module for "
                                  "{1}".format(value, self.__class__))
        self._modulename = value
        self._validation_context = ValidationContext(value)

        try:
            self._strategy = self._get_production_strategy()
        except ValidationError as e:
            self._validation_errors.add(e)

        try:
            self._get_changelog()
        except ValidationError as e:
            self._validation_errors.add(e)

    @property
    def desc(self):
        raise NotImplementedError

    def _get_production_strategy(self):
        raise NotImplementedError

    def _get_status(self):
        raise NotImplementedError

    @property
    def obom(self):
        raise NotImplementedError

    @property
    def bom(self):
        raise NotImplementedError

    @property
    def _changelogpath(self):
        raise NotImplementedError

    def make_labels(self, sno, label_manager=None):
        raise NotImplementedError

    @property
    def projfolder(self):
        raise NotImplementedError

    def _register_for_changes(self):
        pass

    def reload(self):
        # TODO Signal all other threads to reload.
        self._reload()

    def _reload(self):
        # Not handled :
        #   - Name changes
        #   - Ripple effects to any downstream objects
        self._validation_errors = ErrorCollector()
        self._configs = None
        self._bom = None
        self._obom = None
        self._status = None
        self._strategy = None
        self._changelog = None
        self.ident = self._modulename
        self.validate()

    def _validate(self):
        raise NotImplementedError


class EDAProjectPrototype(ModulePrototypeBase):
    def __init__(self, modulename):
        super(EDAProjectPrototype, self).__init__(modulename)

    @property
    def ident(self):
        return self._modulename

    @ident.setter
    def ident(self, value):
        raise NotImplementedError

    @property
    def projfolder(self):
        raise NotImplementedError

    def make_labels(self, sno, label_manager=None):
        pass

    @property
    def configs(self):
        if not self._configs:
            self._configs = ConfigsFile(self.projfolder)
        return self._configs

    def _get_status(self):
        self._status = self.configs.status

    @property
    def obom(self):
        raise NotImplementedError

    @property
    def bom(self):
        raise NotImplementedError

    def _get_production_strategy(self):
        raise NotImplementedError

    @property
    def desc(self):
        try:
            return self.configs.description()
        except KeyError:
            return None

    @property
    def _changelogpath(self):
        return os.path.join(self.projfolder, 'ChangeLog')

    def _validate(self):
        # TODO Verify PCB size, layers
        pass

    @property
    def rprojfolder(self):
        return os.path.relpath(self.projfolder, PROJECTS_ROOT)


class CableProjectPrototype(EDAProjectPrototype):
    @property
    def ident(self):
        return self._modulename

    @ident.setter
    def ident(self, value):
        if value not in projects.cable_projects.keys():
            raise ModuleNotRecognizedError(
                "Cable Project {0} not recognized".format(value))
        self._modulename = value
        self._validation_context = ValidationContext(value)

        try:
            self._get_changelog()
        except ValidationError as e:
            self._validation_errors.add(e)

    @property
    def projfolder(self):
        return projects.cable_projects[self.ident]


class PCBPrototype(EDAProjectPrototype):
    def __init__(self, modulename):
        super(PCBPrototype, self).__init__(modulename)
        self._indicative_sourcing_info = None
        self._pcb_info = None

    @property
    def ident(self):
        return self._modulename

    @ident.setter
    def ident(self, value):
        if value not in projects.pcbs.keys():
            raise ModuleNotRecognizedError(
                    "PCB {0} not recognized".format(value))
        self._modulename = value
        self._validation_context = ValidationContext(value)

        try:
            self._get_changelog()
        except ValidationError as e:
            self._validation_errors.add(e)

    @property
    def projfolder(self):
        return projects.pcbs[self.ident]

    @property
    def indicative_sourcing_info(self):
        if self._indicative_sourcing_info is None:
            from tendril.inventory.guidelines import electronics_qty
            from tendril.sourcing.electronics import get_sourcing_information
            from tendril.sourcing.electronics import SourcingException
            iqty = electronics_qty.get_compliant_qty(self.ident, 1)
            try:
                ident = 'PCB ' + self.ident
                vsi = get_sourcing_information(ident, iqty,
                                               allvendors=True)
            except SourcingException:
                vsi = []
            self._indicative_sourcing_info = vsi
        return self._indicative_sourcing_info

    @property
    def info(self):
        if not self._pcb_info:
            from tendril.gedaif.pcb import get_pcbinfo
            from tendril.gedaif.projfile import GedaProjectFile
            pf = GedaProjectFile(self.projfolder)
            pcbf = os.path.join(self.projfolder, 'pcb', pf.pcbfile + '.pcb')
            self._pcb_info = get_pcbinfo(pcbf)
        return self._pcb_info

    @property
    def docs(self):
        return get_docs_list(self.projfolder)


class EDAModulePrototypeBase(ModulePrototypeBase):
    @property
    def projectname(self):
        raise NotImplementedError

    @property
    def rprojfolder(self):
        return os.path.relpath(self.projfolder, PROJECTS_ROOT)

    @property
    def desc(self):
        return self.configs.description(self.ident)

    @property
    def configs(self):
        if not self._configs:
            self._configs = ConfigsFile(self.projfolder)
        return self._configs

    @property
    def bom(self):
        if not self._bom:
            self._bom = EntityElnBom(self.configs)
            self._bom.configure_motifs(self.ident)
        return self._bom

    @property
    def obom(self):
        if not self._obom:
            self._obom = self.bom.create_output_bom(configname=self.ident)
        return self._obom

    def _get_status(self):
        raise NotImplementedError

    @property
    def _psctx(self):
        ctx = copy(self._validation_context)
        ctx.locality = 'Strategy'
        return ctx

    @property
    def _pspol_doc_am(self):
        return ConfigOptionPolicy(
            context=self._psctx, path=('documentation', 'am'),
            options=[True, False], is_error=True, default=True
        )

    @property
    def _pspol_testing(self):
        return ConfigOptionPolicy(
            context=self._psctx, path=('productionstrategy', 'testing'),
            options=['normal', 'lazy'], is_error=True, default='normal'
        )

    @property
    def _pspol_labelling(self):
        return ConfigOptionPolicy(
            context=self._psctx, path=('productionstrategy', 'labelling'),
            options=['normal', 'lazy'], is_error=True, default='normal'
        )

    @property
    def _pspol_labeldefs(self):
        return ConfigOptionPolicy(
            context=self._psctx, path=('documentation', 'labels'),
            options=None, is_error=True, default=None
        )

    def _get_production_strategy(self):
        rval = {}
        configdata = self.configs.rawconfig
        ec = ErrorCollector()

        try:
            am = get_dict_val(configdata, self._pspol_doc_am)
        except ValidationError as e:
            am = e.policy.default
            ec.add(e)
        if am is True:
            # Assembly manifest should be used
            rval['prodst'] = "@AM"
            rval['genmanifest'] = True
        else:
            # No Assembly manifest needed
            rval['prodst'] = "@THIS"
            rval['genmanifest'] = False

        try:
            testing = get_dict_val(configdata, self._pspol_testing)
        except ValidationError as e:
            testing = e.policy.default
            ec.add(e)
        if testing == 'normal':
            # Normal test procedure, Test when made
            rval['testst'] = "@NOW"
        if testing == 'lazy':
            # Lazy test procedure, Test when used
            rval['testst'] = "@USE"

        try:
            labelling = get_dict_val(configdata, self._pspol_labelling)
        except ValidationError as e:
            labelling = e.policy.default
            ec.add(e)
        if labelling == 'normal':
            # Normal test procedure, Label when made
            rval['lblst'] = "@NOW"
        if labelling == 'lazy':
            # Lazy test procedure, Label when used
            rval['lblst'] = "@USE"
        rval['genlabel'] = False
        rval['labels'] = []

        try:
            labeldefs = get_dict_val(configdata, self._pspol_labeldefs)
        except ValidationError as e:
            labeldefs = e.policy.default
            ec.add(e)

        if labeldefs is not None:
            if isinstance(labeldefs, dict):
                for k in sorted(labeldefs.keys()):
                    rval['labels'].append(
                        {'code': k,
                         'ident': self.ident + '.' + configdata['label'][k]}
                    )
                rval['genlabel'] = True
            elif isinstance(labeldefs, str):
                rval['labels'].append(
                    {'code': labeldefs,
                     'ident': self.ident}
                )
                rval['genlabel'] = True
        return rval

    def make_labels(self, sno, label_manager=None):
        # This does not check whether the sno is valid and correct and
        # so on. This should therefore not be called directly, but instead
        # the instance's makelabel function should be used.
        if label_manager is None:
            from tendril.dox.labelmaker import manager
            label_manager = manager
        if self.strategy['genlabel'] is True:
            for label in self.strategy['labels']:
                label_manager.add_label(
                    label['code'], label['ident'], sno
                )

    @property
    def _changelogpath(self):
        return os.path.join(self.projfolder, 'ChangeLog')

    @property
    def projfolder(self):
        return projects.cards[self.ident]

    @property
    def indicative_cost(self):
        return self.obom.indicative_cost

    @property
    def sourcing_errors(self):
        if self._sourcing_errors is None:
            self._sourcing_errors = self.obom.sourcing_errors
        return self._sourcing_errors

    @property
    def indicative_cost_breakup(self):
        return self.obom.indicative_cost_breakup

    @property
    def indicative_cost_hierarchical_breakup(self):
        try:
            return self.bom.indicative_cost_hierarchical_breakup(self.ident)
        except NoStructureHereException:
            return self.indicative_cost_breakup

    def _validate_obom(self, ec):
        # Final Validation of Output BOMs. This validation is of the
        # ultimate BOM generated, a last check after all possible
        # transformations are complete.

        # On-construction validation of OBOMs only includes the
        # specific mechanisms for construction and transformation,
        # and not validation of the output itself. The output is
        # therefore done here, at the very last minute.

        # NOTE Tentatively, validation errors are to be reported at the
        # instant when the data required to fully explain the error is
        # about to go out of immediately accessible scope.

        obom = self.obom
        ctx = copy(self._validation_context)
        ctx.locality = "OBOM"
        for line in obom.lines:
            policy = IdentPolicy(ctx, projects.is_recognized)
            try:
                policy.check(line.ident, line.refdeslist, self.status)
            except ValidationError as e:
                ec.add(e)
            policy = IdentQtyPolicy(ctx, True)
            try:
                temp = line.quantity
            except (ValueError, ParseException):
                ec.add(QuantityTypeError(policy, line.ident, line.refdeslist))

    def _validate(self):
        # One Time Validators
        temp = self.configs
        temp = self.status
        temp = self.strategy
        temp = self.changelog
        temp = self.bom

        # Validators for Reconstructed Structures
        lvalidation_errors = ErrorCollector()
        # Validate all OBOM line devices
        # Validate all OBOM line idents
        # Validate all OBOM line quantity types
        self._validate_obom(lvalidation_errors)
        self._sourcing_errors = self.obom.sourcing_errors
        # TODO Check for valid snoseries
        # TODO Check for empty groups?
        # TODO Check for unused motifs?
        # TODO Validate all motifs as configured
        # TODO Validate all SJs are accounted for
        # TODO Validate all Generators are expected
        # TODO Higher order configuration validation
        self._validated = True
        return lvalidation_errors

    @property
    def validation_errors(self):
        # Regenerate Validation reconstructed structures
        lverrors = self._validate()
        rval = ErrorCollector()
        rval.add(self._validation_errors)
        # Obtain validation errors from Configs load
        rval.add(self._configs.validation_errors)
        # Obtain validation errors collected during construction
        # from Parser -> BOM -> OBOM
        rval.add(self._obom.validation_errors)
        rval.add(lverrors)
        return rval

    @property
    def docs(self):
        return get_docs_list(self.projfolder, self.ident)


class CardPrototype(EDAModulePrototypeBase):
    prevalidator = staticmethod(projects.check_module_is_card)

    @property
    def pcbname(self):
        return self.bom.configurations.rawconfig['pcbname']

    @property
    def projectname(self):
        return self.pcbname

    def _get_status(self):
        self._status = self.configs.status_config(self.ident)

    def __repr__(self):
        return '<CardPrototype {0}>'.format(self.ident)


class CablePrototype(EDAModulePrototypeBase):
    prevalidator = staticmethod(projects.check_module_is_cable)

    def __repr__(self):
        return '<CablePrototype {0}>'.format(self.ident)

    def _get_status(self):
        return None

    @property
    def cblname(self):
        return self.bom.configurations.rawconfig['cblname']

    @property
    def projectname(self):
        return self.cblname


def get_module_prototype(modulename):
    if projects.check_module_is_card(modulename):
        return CardPrototype(modulename)
    if projects.check_module_is_cable(modulename):
        return CablePrototype(modulename)


class ModuleInstanceBase(EntityBase):
    prevalidator = None

    def __init__(self, sno=None, ident=None, create=False,
                 scaffold=False, session=None):
        super(ModuleInstanceBase, self).__init__()
        self._prototype = None
        self._obom = None
        self._customization = None
        self._ident = None
        if sno is not None:
            self.define(sno, ident, create,
                        scaffold=scaffold, session=session)

    @property
    def ident(self):
        return self._ident

    @ident.setter
    def ident(self, value):
        if value not in projects.cards.keys():
            raise ModuleNotRecognizedError("Module {0} not recognized"
                                           "".format(value))
        if not self.prevalidator(value):
            raise ModuleTypeError("Module {0} is not a not a valid module for"
                                  " {1}".format(value, self.__class__))
        self._ident = value

    def define(self, sno, ident=None, create_new=False,
               register=True, scaffold=False, session=None):
        self._refdes = sno
        if scaffold is True:
            self.ident = ident
            self._defined = True
            return
        if serialnos.serialno_exists(sno=sno, session=session):
            if create_new:
                raise ValueError("Serial Number {0} already exists, cannot be"
                                 " used to create a new instance".format(sno))
            db_ident = serialnos.get_serialno_efield(sno=self._refdes,
                                                     session=session)
            if ident and db_ident != ident:
                raise ModuleInstanceTypeMismatchError(
                        "Module {0} seems to be a {1}, not {2}"
                        "".format(sno, db_ident, ident)
                )
            self.ident = db_ident
            self._defined = True
        else:
            if not create_new:
                raise SerialNoNotFound("Serial Number {0} does not exist, and"
                                       "creation of a new instance is not "
                                       "requested".format(sno))
            else:
                self.ident = ident
                self._defined = True
                raise NotImplementedError(
                        "Registration of serial number of modules should be "
                        "done at the production order level. Registering "
                        "module instances directly is not supported. Once you"
                        " have the serial numbers registered, you can come "
                        "here to fill in the rest.")

    @property
    def prototype(self):
        if self._prototype is None:
            self._prototype = get_module_prototype(self._ident)
        return self._prototype


class EDAModuleInstanceBase(ModuleInstanceBase):
    @property
    def obom(self):
        if self._obom is None:
            bomobj = deepcopy(self.prototype.bom)
            if self._customization is not None:
                raise NotImplementedError(
                        "gEDA Bom customization not yet implemented"
                )
            self._obom = bomobj.create_output_bom(configname=self.ident)
        return self._obom

    def make_labels(self, label_manager=None):
        self.prototype.make_labels(self._refdes, label_manager=label_manager)

    @property
    def projfolder(self):
        return self._prototype.projfolder


class CardInstance(EDAModuleInstanceBase):
    prevalidator = staticmethod(projects.check_module_is_card)

    def __repr__(self):
        if self._customization is not None:
            customized = ' Customized'
        else:
            customized = ''
        return "<CardInstance {0} {1}{2}>".format(
                self.ident, self.refdes, customized
        )

    @property
    def pcbname(self):
        return self._prototype.pcbname


class CableInstance(EDAModuleInstanceBase):
    prevalidator = staticmethod(projects.check_module_is_cable)

    def __repr__(self):
        if self._customization is not None:
            customized = ' Customized'
        else:
            customized = ''
        return '<CableInstance {0} {1}{2}>'.format(
                self.ident, self.refdes, customized
        )

    @property
    def cblname(self):
        return self._prototype.cblname


def get_module_instance(sno, ident=None, scaffold=False, session=None):
    if not scaffold:
        modulename = serialnos.get_serialno_efield(sno=sno,
                                                   session=session)
    else:
        modulename = ident
    if projects.check_module_is_card(modulename):
        return CardInstance(sno=sno, ident=ident,
                            scaffold=scaffold, session=session)
    if projects.check_module_is_cable(modulename):
        return CableInstance(sno=sno, ident=ident,
                             scaffold=scaffold, session=session)


prototypes = {}
projectmap = {}


def get_prototype_lib(regen=False):
    global prototypes
    if regen is False and prototypes:
        return prototypes
    logger.debug("Generating Prototype Library")
    prototypes = {}
    for ident in projects.cards.keys():
        _get_prototype(ident)
    logger.debug("Prototype Library Generated")
    return prototypes


def get_projectmap():
    global projectmap
    if not projectmap:
        get_prototype_lib()
    return projectmap


def _get_prototype(ident):
    global prototypes
    if ident in prototypes.keys():
        return prototypes[ident]

    try:
        prototypes[ident] = CardPrototype(ident)
        pf = prototypes[ident].projfolder
        if pf in projectmap.keys():
            projectmap[pf].append(ident)
        else:
            projectmap[pf] = [ident]
        return
    except ModuleTypeError:
        pass

    try:
        prototypes[ident] = CablePrototype(ident)
        pf = prototypes[ident].projfolder
        if pf in projectmap.keys():
            projectmap[pf].append(ident)
        else:
            projectmap[pf] = [ident]
        return
    except ModuleTypeError:
        pass

    # TODO Raise a validation error here instead?
    raise ModuleTypeError("Could not determine type for ident {0}"
                          "".format(ident))


def get_prototype(ident):
    plib = get_prototype_lib()
    return plib[ident]


pcbs = {}


def get_pcb_lib(regen=False):
    global pcbs
    if regen is False and pcbs:
        return pcbs
    pcbs = {}
    for pcbname, folder in viewitems(projects.pcbs):
        pcbs[pcbname] = PCBPrototype(pcbname)
    return pcbs


projectlib = {}


def get_project_lib(regen=False):
    global projectlib
    if regen is False and projectlib:
        return projectlib
    projectlib = {}
    for project, folder in viewitems(projects.pcbs):
        projectlib[project] = PCBPrototype(project)
    for project, folder in viewitems(projects.cable_projects):
        projectlib[project] = CableProjectPrototype(project)
    return projectlib


def fill_prototype_lib():
    tlen = len(get_prototype_lib().keys())
    count = 0
    for k, prototype in viewitems(get_prototype_lib()):
        count += 1
        logger.info("{0:3}/{1:3} Validating {2}".format(count, tlen, k))
        prototype.validate()


def prep_persistance():
    build_times = []

    logger.info('Building Prototype Library')
    l_start_time = timeit.default_timer()
    get_prototype_lib()
    build_times.append(('prototypelib.build',
                        timeit.default_timer() - l_start_time))

    logger.info('Filling Prototype Library')
    l_start_time = timeit.default_timer()
    fill_prototype_lib()
    build_times.append(('prototypelib.fill',
                        timeit.default_timer() - l_start_time))

    logger.info('Building PCB Library')
    l_start_time = timeit.default_timer()
    get_pcb_lib()
    build_times.append(('pcblib.build',
                        timeit.default_timer() - l_start_time))

    logger.info('Building Project Library')
    l_start_time = timeit.default_timer()
    get_project_lib()
    build_times.append(('projectlib.build',
                        timeit.default_timer() - l_start_time))

    for k, t in build_times:
        logger.info('{0:25} : {1:>5.1f} seconds'.format(k, t))

    try:
        _m = mq.monitor_start('published_vcs_commits', _vcs_commit_handler)
        logger.info("Started VCS Commit Monitor")
    except mq.MQServerUnavailable:
        _m = None
    return _m


def _vcs_commit_handler(data):
    # TODO
    # This piece of code is extremely dangerous, and creates very real
    # scope for race conditions resulting in potential data loss, data
    # mangling, and other unpredicatable outcomes. Utilization of the
    # module / prototype library needs to be protected across the codebase
    # and updates in between transactions should be avoided. How this
    # can / should be implemented is currently unknown.
    #
    # One possible solution may be to include threading locks within each
    # module, and anything using the module should also claim the lock.
    # This seems like it could break all manner of stuff, not to mention
    # would be very difficult to implement.
    #
    # A workable solution may be to allow transactions which care about
    # validity of the data to claim a counting lock on the prototype, and
    # updates should be delayed until all such locks are released.
    #
    # As of this writing, the prototypes are almost exclusively read-only
    # in their usage. In the rare cases where they need to be modified,
    # they are first copied using deepcopy. This should be explicitly
    # verified across the codebase.
    commit_info = json.loads(data)
    repo = commit_info['repo']
    vcsdir = os.path.join(SVN_ROOT, repo)
    targets = [vcsdir]
    lprojects, lpcbs, lcards, lcard_reporoot, lcable_projects = \
        projects.get_projects(vcsdir)
    targets.extend([lprojects[x] for x in lprojects.keys()])
    modulenames = []
    for target in targets:
        try:
            modulenames.extend(get_projectmap()[target])
        except KeyError:
            pass
    _ = [get_prototype(x).reload() for x in modulenames]
    return


if WARM_UP_CACHES is True:
    monitor = prep_persistance()

