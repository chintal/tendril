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
"""
gEDA ConfigsFile module documentation (:mod:`gedaif.conffile`)
==============================================================
"""

import os
from decimal import Decimal

from tendril.boms.configbase import ConfigBase
from tendril.boms.configbase import NoProjectError

from tendril.conventions import status

from tendril.boms.validate import ValidationError
from tendril.boms.validate import ConfigOptionPolicy
from tendril.boms.validate import get_dict_val


class NoGedaProjectError(NoProjectError):
    pass


class ConfigsFile(ConfigBase):
    schema_name = 'pcbconfigs'
    schema_version_max = Decimal("1.0")
    schema_version_min = Decimal("1.0")

    NoProjectErrorType = NoGedaProjectError

    def __init__(self, projectfolder):
        super(ConfigsFile, self).__init__(projectfolder)
        self.projectfile = self._configdata['projfile']
        self._cached_status = None

    @property
    def _cfpath(self):
        return os.path.join(self.projectfolder, "schematic", "configs.yaml")

    def validate(self):
        super(ConfigsFile, self).validate()

    @property
    def projectname(self):
        if self.pcbname is not None:
            return self.pcbname
        else:
            return self.cblname

    @property
    def pcbname(self):
        if self.is_pcb:
            return self._configdata['pcbname']
        else:
            return None

    @property
    def cblname(self):
        if self.is_cable:
            return self._configdata['cblname']
        else:
            return None

    @property
    def is_pcb(self):
        if 'pcbname' in self._configdata.keys() and \
                self._configdata['pcbname'] is not None:
            return True
        else:
            return False

    @property
    def is_cable(self):
        if 'cblname' in self._configdata.keys() and \
                self._configdata['cblname'] is not None:
            return True
        else:
            return False

    @property
    def mactype(self):
        if 'mactype' in self._configdata:
            return self._configdata['mactype']
        else:
            raise AttributeError("No MACTYPE defined for this project")

    def status_config(self, configname):
        if self.status_forced:
            return self.status
        configuration = self.configuration(configname)
        if 'status' in configuration.keys():
            try:
                return status.get_status(configuration['status'])
            except KeyError:
                pass
        else:
            return self.status

    @property
    def status(self):
        # TODO This is horribly ugly. Consider serious refactoring.
        if self._cached_status is None:
            allowed_status_values = status.allowed_status_values()
            allowed_status_values += ['!' + x
                                      for x in status.allowed_status_values()]
            if 'pcbdetails' in self._configdata.keys():
                try:
                    policy = ConfigOptionPolicy(
                        self._validation_context,
                        ('pcbdetails', 'status'),
                        allowed_status_values,
                        default='Experimental',
                        is_error=True
                    )
                    ststr = get_dict_val(self._configdata, policy)
                except ValidationError as e:
                    ststr = e.policy.default
                    self._validation_errors.add(e)
            elif 'paneldetails' in self._configdata.keys():
                try:
                    policy = ConfigOptionPolicy(
                        self._validation_context,
                        ('paneldetails', 'status'),
                        allowed_status_values,
                        default='Experimental',
                        is_error=True
                    )
                    ststr = get_dict_val(self._configdata, policy)
                except ValidationError as e:
                    ststr = e.policy.default
                    self._validation_errors.add(e)
            else:
                e = ValidationError(ConfigOptionPolicy(
                        self._validation_context,
                        'pcbdetails', is_error=True)
                )
                e.detail = "Status not defined or not found in config file."
                ststr = None
                self._validation_errors.add(e)

            if ststr and self.status_forced:
                ststr = ststr[1:]
        else:
            ststr = self._cached_status
        return status.get_status(ststr)

    @property
    def status_forced(self):
        try:
            if 'pcbdetails' in self._configdata.keys():
                ststr = self._configdata['pcbdetails']['status']
            elif 'paneldetails' in self._configdata.keys():
                ststr = self._configdata['paneldetails']['status']
            else:
                return False
        except KeyError:
            return False
        if ststr.startswith('!'):
            return True
        return False

    @property
    def pcbdescriptors(self):
        rval = [str(self._configdata['pcbdetails']['params']['dX']) + 'mm x ' +
                str(self._configdata['pcbdetails']['params']['dY']) + 'mm']
        if self._configdata['pcbdetails']["params"]["layers"] == 2:
            rval.append("Double Layer")
        elif self._configdata['pcbdetails']["params"]["layers"] == 4:
            rval.append("ML4")
        # HAL, Sn, Au, PBFREE, H, NP, I, OC
        if self._configdata['pcbdetails']["params"]["finish"] == 'Au':
            rval.append("Immersion Gold/ENIG finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'Sn':
            rval.append("Immersion Tin finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'PBFREE':
            rval.append("Any Lead Free finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'H':
            rval.append("Lead F ree HAL finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'NP':
            rval.append("No Copper finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'I':
            rval.append("OSP finish")
        elif self._configdata['pcbdetails']["params"]["finish"] == 'OC':
            rval.append("Only Copper finish")
        else:
            rval.append("UNKNOWN FINISH: " +
                        self._configdata['pcbdetails']["params"]["finish"])
        return rval
