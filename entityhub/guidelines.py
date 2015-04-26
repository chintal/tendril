"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import yaml
from decimal import Decimal


class QtyGuidelines(object):
    def __init__(self, guidelinefile):
        self._idents = None
        self._generators = None
        self._devices = None
        self._guidelinefile = guidelinefile
        self._load_guidelines()

    def _load_guidelines(self):
        with open(self._guidelinefile, 'r') as f:
            data = yaml.load(f)
            self._idents = data['idents']
            self._generators = data['generators']
            self._devices = data['devices']

    @staticmethod
    def _get_full_guideline(gldict):
        if 'oqty_min' in gldict.keys():
            oqty_min = int(gldict['oqty_min'])
        else:
            oqty_min = 1
        if 'oqty_multiple' in gldict.keys():
            oqty_multiple = int(gldict['oqty_multiple'])
        else:
            oqty_multiple = 1
        if 'baseline_qty' in gldict.keys():
            baseline_qty = int(gldict['baseline_qty'])
        else:
            baseline_qty = 0
        if 'excess_min_pc' in gldict.keys():
            excess_min_pc = Decimal(gldict['excess_min_pc'])
        else:
            excess_min_pc = 0
        if 'excess_max_qty' in gldict.keys():
            excess_max_qty = int(gldict['excess_max_qty'])
        else:
            excess_max_qty = -1
        return oqty_min, oqty_multiple, baseline_qty, excess_min_pc, excess_max_qty

    def get_compliant_qty(self, ident, qty,
                          handle_excess=True,
                          except_on_overrun=True,
                          handle_baseline=False,
                          ):
        gldict = None
        if ident in self._idents.keys():
            gldict = self._idents[ident]
        oqty = qty
        if gldict is not None:
            oqty_min, oqty_multiple, baseline_qty, excess_min_pc, excess_max_qty = self._get_full_guideline(gldict)
            tqty = qty
            if handle_excess is True:
                tqty *= 1 + Decimal(excess_min_pc) / 100
            if tqty <= oqty_min:
                oqty = oqty_min
            else:
                oqty = oqty_min
                while oqty <= tqty:
                    oqty += oqty_multiple
            if handle_excess is True:
                excess = oqty - qty
                if 0 < excess_max_qty < excess:
                    logger.warning('Maximum Excess Quantity exceeds predefined maximum : ' +
                                   ident + "::" + str((qty, oqty, excess_max_qty)))
                    if except_on_overrun is True:
                        raise ValueError
        return oqty
