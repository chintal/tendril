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
Docstring for LM3150.py

.. seealso:: Section 9.2.2.1 of the
             `LM3150 datasheet<http://www.ti.com/lit/ds/symlink/lm3150.pdf>`_
"""

import itertools
import iec60063

from tendril.conventions.motifs.motifbase import MotifBase
from tendril.conventions import electronics
from tendril.gedaif import gsymlib

from decimal import Decimal
from tendril.utils.types.electromagnetic import Voltage
from tendril.utils.types.electromagnetic import Current
from tendril.utils.types.electromagnetic import Resistance
from tendril.utils.types.electromagnetic import Inductance
from tendril.utils.types.electromagnetic import Capacitance
from tendril.utils.types.electromagnetic import Charge
from tendril.utils.types.time import Frequency
from tendril.utils.types.time import TimeSpan
from tendril.utils.types.electromagnetic import DutyCycle
from tendril.utils.types.unitbase import Percentage

from tendril.utils import log
logger = log.get_logger(__name__, log.DEFAULT)


class MotifLM3150(MotifBase):
    def __init__(self, identifier):
        super(MotifLM3150, self).__init__(identifier)
        self._configdict = None

    def _get_Vout(self, rfb1, rfb2):
        rval = self._vref * \
            ((Resistance(rfb1) + Resistance(rfb2)) / Resistance(rfb1))
        return rval

    def _set_vout(self, target_vout):
        if not isinstance(target_vout, Voltage):
            target_vout = Voltage(target_vout)

        rfb1_dev = self.get_elem_by_idx('RFB1').data['device']
        rfb1_fp = self.get_elem_by_idx('RFB1').data['footprint']
        rfb2_dev = self.get_elem_by_idx('RFB2').data['device']
        rfb2_fp = self.get_elem_by_idx('RFB2').data['footprint']
        if rfb1_fp[0:3] == "MY-":
            rfb1_fp = rfb1_fp[3:]
        if rfb2_fp[0:3] == "MY-":
            rfb2_fp = rfb2_fp[3:]

        allowed_rfb1_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                              iec60063.res_ostrs,
                                              start='8.2K',
                                              end='10K')

        allowed_rfb2_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                              iec60063.res_ostrs,
                                              self._configdict['Rmin'],
                                              self._configdict['Rmax'])

        allowed_rfb1_vals = [x for x in allowed_rfb1_vals]
        allowed_rfb2_vals = [x for x in allowed_rfb2_vals]
        best_match = None

        for pair in itertools.product(allowed_rfb1_vals, allowed_rfb2_vals):
            vout = self._get_Vout(*pair)
            error = abs(vout - target_vout)
            if best_match is None or error < best_match[1]:
                best_match = (vout, error, pair[0], pair[1])

        rfb1_value = gsymlib.find_resistor(best_match[2], rfb1_fp, rfb1_dev)
        self.get_elem_by_idx('RFB1').data['value'] = rfb1_value

        rfb2_value = gsymlib.find_resistor(best_match[3], rfb2_fp, rfb2_dev)
        self.get_elem_by_idx('RFB2').data['value'] = rfb2_value

    def _get_fsw(self, ron):
        if not isinstance(ron, Resistance):
            ron = Resistance(ron)
        return Frequency(
            self.Vout.value / (Charge('100pC').value * ron.value)
        )

    def _autoset_fsw(self):
        ron_dev = self.get_elem_by_idx('RON').data['device']
        ron_fp = self.get_elem_by_idx('RON').data['footprint']

        self.d_min = DutyCycle(
            100 * self.Vout / self.Vin_max
        )

        self.d_max = DutyCycle(
            100 * self.Vout / self.Vin_min
        )

        self.ton_min = TimeSpan(self._configdict['Ton_min'])
        self.fs_max_ontime = self.d_min / self.ton_min

        self.toff_min = TimeSpan(self._configdict['Toff_min']) + \
            TimeSpan(self._configdict['Toff_fet'])
        self.fs_max_offtime = (1 - self.d_max.value / 100) / self.toff_min

        self.fs_max = Percentage('80%') * min([self.fs_max_ontime, self.fs_max_offtime])  # noqa

        self.target_ron = Resistance(
            self.Vout.value / (Charge('100pC').value * self.fs_max.value)
        )

        allowed_ron_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        best_match = None
        for r in allowed_ron_vals:
            fsw = self._get_fsw(r)
            if self.fs_max > fsw:
                if best_match is None or fsw > best_match[0]:
                    best_match = (fsw, r)

        ron_value = gsymlib.find_resistor(best_match[1], ron_fp, ron_dev)
        self.get_elem_by_idx('RON').data['value'] = ron_value

    def _autoset_Cff(self):
        cff_dev = self.get_elem_by_idx('CFF').data['device']
        cff_fp = self.get_elem_by_idx('CFF').data['footprint']

        Zfb = self.RFB1 * (self.RFB2 / (self.RFB1 + self.RFB2))
        self.target_cff = Capacitance(
            (self.Vout / self.Vin_min) / (self.Fsw.value * Zfb.value)
        )

        allowed_cff_vals = iec60063.gen_vals(self._configdict['Cseries'],
                                             iec60063.cap_ostrs,
                                             self._configdict['Cmin'],
                                             self._configdict['Cmax'])

        best_match = None
        for c in allowed_cff_vals:
            err = abs(self.target_cff - Capacitance(c))
            if best_match is None or err < best_match[0]:
                best_match = (err, c)

        cff = gsymlib.find_capacitor(best_match[1], cff_fp, cff_dev)
        self.get_elem_by_idx('CFF').data['value'] = cff.value

    def _autoset_ET(self):
        dropmax = self.Vin_max - self.Vout
        ratiomax = self.Vout / self.Vin_max
        self.ET_max = dropmax.value * ratiomax * (1000000 / self.Fsw).value

        dropmin = self.Vin_min - self.Vout
        ratiomin = self.Vout / self.Vin_min
        self.ET_min = dropmin.value * ratiomin * (1000000 / self.Fsw).value

    def _autoset_Co(self):
        Co_min_k = (Decimal(70))
        self.Co_min = Capacitance(
            Co_min_k / ((self.Fsw.value ** 2) * self.L1.value)
        )

        self.Co_ESR_max = Resistance(
            1000000 * Voltage('80mV').value * self.L1.value / self.ET_min
        )

        self.Co_ESR_min_1 = Resistance(
            1000000 * Voltage('15mV').value * self.L1.value / self.ET_max
        )

        self.Co_ESR_min_2 = Resistance(
            self.ET_max / ((self.Vin_typ - self.Vout).value * self.CO.value * 1000000)  # noqa
        )

        self.Co_ESR_min = max(self.Co_ESR_min_1, self.Co_ESR_min_2)
        self.Co_eff = self._configdict['Co_mult'] * Capacitance(self._configdict['Co_num'])  # noqa
        self.Co_ESR_eff = Resistance(self._configdict['Co_esr']) / self._configdict['Co_mult']  # noqa

    def _autoset_fet(self):
        self.fet_Vds_min = Decimal(1.2) * self.Vin_max

        self.fet_Qgtotal_max = Charge(Current('65mA').value / self.Fsw.value)
        self.fet_Qgh = Charge(self._configdict['fet_Qg_hs_5V'])
        self.fet_Qgl = Charge(self._configdict['fet_Qg_ls_6V'])
        self.fet_Qgtotal = self.fet_Qgh + self.fet_Qgl

        self.fet_Rdson = Resistance(self._configdict['fet_Rdson'])
        logger.debug('Rdson: {0}'.format(self.fet_Rdson))

        d_typ = DutyCycle(100 * self.Vout / self.Vin_typ)
        self.Pcond = self.Iout.value ** 2 * self.fet_Rdson.value * d_typ.value / 100  # noqa

        # This results in about 10 times greater dissipation than the
        # datasheet calculation, due to 1.5nC used as the gate charge.
        # This difference needs to be resolved.
        psw_t1 = self.Vin_typ.value * self.Iout.value * self.fet_Qgh.value
        vth = 2.5
        psw_t2 = self.Fsw.value * Decimal((8.5 / (6 - vth)) + (6.8 / vth))
        self.Psw = Decimal(0.5) * psw_t1 * psw_t2

        self.Pdh = self.Pcond + self.Psw

        nd = (1 - d_typ.value / 100)
        self.Pdl = self.Iout.value ** 2 * self.fet_Rdson.value * nd

    def _autoset_ilim(self):
        rlim_dev = self.get_elem_by_idx('RLIM').data['device']
        rlim_fp = self.get_elem_by_idx('RLIM').data['footprint']

        icl = self.Iout * Decimal(1.2 - 0.33)

        self.target_rlim = (icl / Current('85uA')) * self.fet_Rdson

        allowed_rlim_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                              iec60063.res_ostrs,
                                              self._configdict['Rmin'],
                                              self._configdict['Rmax'])

        best_match = None
        for r in allowed_rlim_vals:
            r = Resistance(r)
            if r > self.target_rlim:
                if best_match is None or r < best_match:
                    best_match = r

        rlim_value = gsymlib.find_resistor(best_match, rlim_fp, rlim_dev)
        self.get_elem_by_idx('RLIM').data['value'] = rlim_value

    def _autoset_Ci(self):
        vin_ripple = self.Vin_max_ripple_pc * self.Vin_typ
        d_typ = self.Vout / self.Vin_typ
        self.Ci_min = Capacitance(
            (self.Iout.value * d_typ * (1-d_typ)) / (self.Fsw.value * vin_ripple.value)  # noqa
        )
        self.Ci_imin = self.Iout / 2
        self.Ci_eff = self._configdict['Ci_mult'] * Capacitance(self._configdict['Ci_num'])  # noqa
        self.Ci_ESR_eff = Resistance(self._configdict['Ci_esr']) / self._configdict['Ci_mult']  # noqa
        self.Cdi_min = 5 * self.Ci_eff
        self.Vin_ripple = Voltage(self.Iout.value * d_typ * (1-d_typ) / (self.Ci_eff.value * self.Fsw.value))  # noqa

    def _set_part_nos(self):
        for idx in range(self._configdict['Ci_mult_max']):
            self.get_elem_by_idx('CIN' + str(idx)).data['value'] = self._configdict['Ci_pno']  # noqa
            if idx >= self._configdict['Ci_mult']:
                self.get_elem_by_idx('CIN' + str(idx)).data['fillstatus'] = 'DNP'  # noqa

        for idx in range(self._configdict['Co_mult_max']):
            self.get_elem_by_idx('COUT' + str(idx)).data['value'] = self._configdict['Co_pno']  # noqa
            if idx >= self._configdict['Co_mult']:
                self.get_elem_by_idx('COUT' + str(idx)).data['fillstatus'] = 'DNP'  # noqa

        self.get_elem_by_idx('L1').data['value'] = self._configdict['L_pno']
        self.get_elem_by_idx('CDIN').data['value'] = self._configdict['Cdi_pno']  # noqa

    def configure(self, configdict):
        self._configdict = configdict

        self._vref = Voltage(self._configdict['Vref'])

        self.Vin_max_ripple_pc = Percentage(self._configdict['Vin_ripple'])
        self.Vin_min = Voltage(self._configdict['Vin_min'])
        self.Vin_max = Voltage(self._configdict['Vin_max'])
        if 'Vin_typ' in self._configdict.keys():
            self.Vin_typ = Voltage(self._configdict['Vin_typ'])
        else:
            self.Vin_typ = (self.Vin_max + self.Vin_min) / 2

        self.Vout = Voltage(self._configdict['Vout'])
        self.Iout = Current(self._configdict['Iout'])
        self._set_part_nos()
        self.validate()

    @property
    def Vout(self):
        return self._get_Vout(self.RFB1, self.RFB2)

    @Vout.setter
    def Vout(self, value):
        self._set_vout(target_vout=value)
        self._autoset_fsw()
        self._autoset_Cff()
        self._autoset_ET()

    @property
    def Fsw(self):
        return self._get_fsw(self.RON)

    @property
    def Iout(self):
        return Current(self._configdict['Iout'])

    @Iout.setter
    def Iout(self, value):
        self.L1 = self._configdict['L_num']
        self.CO = self._configdict['Co_num']
        self._autoset_Co()
        self._autoset_fet()
        self._autoset_ilim()
        self._autoset_Ci()

    @property
    def RFB1(self):
        elem = self.get_elem_by_idx('RFB1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def RFB2(self):
        elem = self.get_elem_by_idx('RFB2')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def RON(self):
        elem = self.get_elem_by_idx('RON')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def L1(self):
        return self._l1

    @L1.setter
    def L1(self, value):
        self._l1 = Inductance(value)

    @property
    def CO(self):
        return self._co

    @CO.setter
    def CO(self, value):
        self._co = Capacitance(value)

    @property
    def CFF(self):
        elem = self.get_elem_by_idx('CFF')
        assert elem.data['device'] in ['CAP CER SMD', 'CAP CER THRU']
        return Capacitance(electronics.parse_capacitance(electronics.parse_capacitor(elem.data['value'])[0]))  # noqa

    @property
    def RLIM(self):
        elem = self.get_elem_by_idx('RLIM')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return Resistance(electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0]))  # noqa

    @property
    def Vin_max_ripple(self):
        return self.Vin_max_ripple_pc * self.Vin_typ

    def validate(self):
        pass

    def listing(self):
        pass

    @property
    def parameters_base(self):
        p_derived = [
            ('Vin_typ', "Typical Input Voltage", "(Vin_min + Vin_max)/2"),
        ]
        p_vout = [
            ('RFB1', "Lower Feedback Resistor", ''),
            ('RFB2', "Upper Feedback Resistor", ''),
            ('CFF', "Feed Forward Capacitor", self.target_cff),
            ('Vout', "Actual Output Voltage", self._configdict['Vout']),
        ]
        p_fsw = [
            ('ton_min', "Minimum On Time", ""),
            ('toff_min', "Minimum Off Time", ""),
            ('d_max', "Maximum Duty Cycle", "Vout / Vin_max"),
            ('d_min', "Minimum Duty Cycle", "Vout / Vin_min"),
            ('fs_max_ontime', "Maximum Frequency (on-time)",
             'd_min / Ton_min'),
            ('fs_max_offtime', "Maximum Frequency (off-time)",
             '(1 - d_max) / Toff_min'),
            ('fs_max', "Maximum Frequency", ''),
            ('RON', "On-Time Setting Resistor", self.target_ron),
            ('Fsw', "Actual Switching Frequency", ''),
        ]
        p_l = [
            ('ET_max', "Minimum Volt-Second Constant", ''),
            ('ET_min', "Maximum Volt-Second Constant", ''),
            ('L1', "Inductance", ''),
        ]
        p_co = [
            ('Co_min', "Minimum Ouptut Capacitance", ''),
            ('Co_ESR_max', "Maximum Output Capacitor ESR", ''),
            ('Co_ESR_min', "Minimum Output Capacitor ESR", ''),
            ('Co_eff', "Effective Output Capacitance", ''),
            ('Co_ESR_eff', "Effective Output Capacitor ESR", ''),
        ]
        p_ci = [
            ('Ci_min', "Minimum Input Capacitance", ''),
            ('Ci_imin', "Input Capacitor Minimum RMS Current Rating", ''),
            ('Ci_eff', "Effective Input Capacitance", ''),
            ('Cdi_min', "Minimum Input Damping Capacitor",
             '5 x Input Capacitance'),
            ('Vin_ripple', "Input Voltage Ripple", self.Vin_max_ripple)
        ]
        p_fet = [
            ('fet_Vds_min', "Minimum FET Vds rating", ''),
            ('fet_Qgtotal_max', "Maximum total FET gate charge", ''),
            ('fet_Qgh', "Act. High side FET gate charge", ''),
            ('fet_Qgl', "Act. Low side FET gate charge", ''),
            ('fet_Qgtotal', "Total Act. FET gate charge", ''),
            ('Pcond', "High Side MOSFET Dissipation (Conduction)", ''),
            ('Psw', "High Side MOSFET Dissipation (Switching)", ''),
            ('Pdh', "High Side MOSFET Dissipation", ''),
            ('Pdl', "Low Side MOSFET Dissipation", ''),
        ]
        p_lim = [
            ('RLIM', "Current Limit Resistance", self.target_rlim),
        ]
        parameters = [
            (p_derived, "Derived Parameters"),
            (p_vout, "Output Voltage Setting"),
            (p_fsw, "Switching Frequency Selection"),
            (p_l, "Inductor Selection"),
            (p_co, "Output Capacitor Selection"),
            (p_ci, "Input Capacitor Selection"),
            (p_fet, "FET Selection"),
            (p_lim, "Current Limit Setting"),
        ]
        return parameters

    @property
    def configdict_base(self):
        inputs = [
            ('desc', 'LM3150 Simple Switcher', 'description', str),
            ('Vref', '0.6V', 'Reference for Output Voltage', Voltage),
            ('Rseries', 'E24', 'Resistance Series', str),
            ('Rmin', '10E', 'Minimum Resistance', str),
            ('Rmax', '10M', 'Maximum Resistance', str),
            ('Cseries', 'E12', 'Capacitance Series', str),
            ('Cmin', '1pF', 'Minimum Capacitance', str),
            ('Cmax', '100nF', 'Maximum Capacitance', str),
            ('Iout', '10A', 'Rated Output Current', Current),
            ('Vin_min', '10V', 'Minimum Input Voltage', Voltage),
            ('Vin_max', '26V', 'Maximum Input Voltage', Voltage),
            ('Ton_min', '200ns', 'Minimum On Time', TimeSpan),
            ('Toff_min', '525ns', 'Minimum Off Time', TimeSpan),
            ('Toff_fet', '200ns', 'MOSFET Turn-off Time', TimeSpan),
            ('fet_Qg_hs_5V', '', 'High Side FET Gate Charge', Charge),
            ('fet_Qg_ls_6V', '', 'Low Side FET Gate Charge', Charge),
            ('fet_Rdson', '', 'MOSFET Rdson', Resistance),
            ('L_num', '', 'Effective Inductance', Inductance),
            ('Co_num', '',
             'Capacitance of Each Output Capacitance', Capacitance),
            ('Co_mult_max', 2,
             "Max Number of Output Capacitors in Parallel", int),
            ('Co_mult', 1, "Number of Output Capacitors in Parallel", int),
            ('Co_esr', '10m', "Output Capacitor ESR", Resistance),
            ('Ci_num', '',
             'Capacitance of Each Input Capacitor', Capacitance),
            ('Ci_mult_max', 3,
             "Max Number of Input Capacitors in Parallel", int),
            ('Ci_mult', 1, "Number of Input Capacitors in Parallel", int),
            ('Ci_esr', '10m', "Input Capacitor ESR", Resistance),
            ('Vout', '', 'Output Voltage', Voltage),
            ('Vin_ripple', '5pc', 'Input Ripple Voltage', Percentage)
        ]
        return inputs
