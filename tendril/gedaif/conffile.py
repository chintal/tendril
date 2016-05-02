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

    @property
    def _cfpath(self):
        return os.path.join(self.projectfolder, "schematic", "configs.yaml")

    def validate(self):
        super(ConfigsFile, self).validate()

    @property
    def pcbname(self):
        if self.is_pcb:
            return self._configdata['pcbname']
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
        try:
            if 'pcbdetails' in self._configdata.keys():
                ststr = self._configdata['pcbdetails']['status']
            elif 'paneldetails' in self._configdata.keys():
                ststr = self._configdata['paneldetails']['status']
            else:
                raise AttributeError('Status not defined or not found for {0}'
                                     ''.format(self._projectfolder))
        except KeyError:
            raise AttributeError('Status not defined or not found for {0}'
                                 ''.format(self._projectfolder))
        if self.status_forced:
            ststr = ststr[1:]
        return status.get_status(ststr)

    @property
    def status_forced(self):
        try:
            if 'pcbdetails' in self._configdata.keys():
                ststr = self._configdata['pcbdetails']['status']
            elif 'paneldetails' in self._configdata.keys():
                ststr = self._configdata['paneldetails']['status']
            else:
                raise AttributeError('Status not defined or not found for {0}'
                                     ''.format(self._projectfolder))
        except KeyError:
            raise AttributeError('Status not defined or not found for {0}'
                                 ''.format(self._projectfolder))
        if ststr.startswith('!'):
            return True

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
