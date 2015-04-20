"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from math import fabs

from conventions.motifs.motifbase import MotifBase
from conventions import electronics
from conventions import iec60063
from gedaif import gsymlib

from utils import log
logger = log.get_logger(__name__, log.INFO)


class MotifLREGS1(MotifBase):
    def __init__(self, identifier):
        super(MotifLREGS1, self).__init__(identifier)
        self._configdict = None

    def get_configdict_stub(self):
        stub = {'desc': 'Positive LDO Output Voltage Setter',
                'regulator': '',
                'Vref': '1.225V',
                'Imin': '1mA',
                'Rseries': 'E12',
                'Rmin': '10E',
                'Rmax': '10M'}
        return stub

    def configure(self, configdict):
        self._configdict = configdict
        self._autoset_r2()
        self.Vout = configdict['Vout']
        self.validate()

    def _autoset_r2(self):
        r2_dev = self.get_elem_by_idx('R2').data['device']
        r2_fp = self.get_elem_by_idx('R2').data['footprint']
        if r2_fp[0:3] == "MY-":
            r2_fp = r2_fp[3:]

        allowed_res_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        required_res_val = fabs(self.Vref * 1000 / self.Imin)

        rval = None
        lastval = None
        for val in allowed_res_vals:
            lastval = rval
            rval = electronics.parse_resistance(val)
            if rval >= required_res_val:
                self.get_elem_by_idx('R2').data['value'] = gsymlib.find_resistor(lastval, r2_fp, r2_dev)
                break

    def validate(self):
        logger.info("Validating Motif : " + self.refdes)
        logger.info(" Vout: " + str(self.Vout) + " R2:" + str(self.R2) + " R1:" + str(self.R1))

    @property
    def Vout(self):
        return self.Vref * (1 + (self.R1 / self.R2))

    @Vout.setter
    def Vout(self, value):
        r1_dev = self.get_elem_by_idx('R1').data['device']
        r1_fp = self.get_elem_by_idx('R1').data['footprint']
        if r1_fp[0:3] == "MY-":
            r1_fp = r1_fp[3:]

        allowed_res_vals = iec60063.gen_vals(self._configdict['Rseries'],
                                             iec60063.res_ostrs,
                                             self._configdict['Rmin'],
                                             self._configdict['Rmax'])

        required_res_val = ((electronics.parse_voltage(value) / self.Vref) - 1) * self.R2

        rval = None
        lastval = None
        for val in allowed_res_vals:
            lastval = rval
            rval = electronics.parse_resistance(val)
            if rval >= required_res_val:
                self.get_elem_by_idx('R1').data['value'] = gsymlib.find_resistor(lastval, r1_fp, r1_dev)
                break

    @property
    def R1(self):
        elem = self.get_elem_by_idx('R1')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0])

    @property
    def R2(self):
        elem = self.get_elem_by_idx('R2')
        assert elem.data['device'] in ['RES SMD', 'RES THRU']
        return electronics.parse_resistance(electronics.parse_resistor(elem.data['value'])[0])

    @property
    def Vref(self):
        return electronics.parse_voltage(self._configdict['Vref'])

    @property
    def Imin(self):
        return electronics.parse_current(self._configdict['Imin'])

    @property
    def Il(self):
        return self.Vref / self.R2


