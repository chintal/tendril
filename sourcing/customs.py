"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.DEFAULT)

import yaml
import os

import vendors
import gedaif.gsymlib
import dox.customs
import utils.currency
from utils.config import CUSTOMSDEFAULTS_FOLDER


class CustomsSection(object):
    def __init__(self, code, hsdict):
        self._code = code
        if 'name' in hsdict.keys():
            self._name = hsdict['name']
        else:
            self._name = None
        if 'idents' in hsdict.keys():
            self._idents = hsdict['idents']
        else:
            self._idents = None
        if 'folders' in hsdict.keys():
            self._folders = hsdict['folders']
        else:
            self._folders = None
        if 'desc' in hsdict.keys():
            self._desc = hsdict['desc']
        else:
            self._desc = None

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def idents(self):
        return self._idents

    @property
    def folders(self):
        return self._folders

    def __repr__(self):
        return "{0:<15} {1}".format(self._code, self.name)


class CustomsClassifier(object):
    def __init__(self):
        self._sections = []
        self._load_sections()

    def _load_sections(self):
        hs_codes_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, 'hs_codes.yaml')
        with open(hs_codes_file, 'r') as f:
            data = yaml.load(f)
            for section, sectiondict in data['sections'].iteritems():
                self._sections.append(CustomsSection(section, sectiondict))

    def hs_from_ident(self, ident):
        for section in self._sections:
            if section.idents is not None:
                for sign in section.idents:
                    if sign in ident:
                        return section
        rsign = ''
        rsec = None
        for section in self._sections:
            if section.folders is not None:
                for sign in section.folders:
                    if sign in gedaif.gsymlib.get_symbol_folder(ident, True):
                        if rsign in sign:
                            rsec = section
                            rsign = sign
        return rsec

hs_classifier = CustomsClassifier()


class CustomsInvoice(vendors.VendorInvoice):
    def __init__(self, vendor, inv_yaml):
        vendor_defaults_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, vendor._name + '.yaml')
        self._data = {}
        if os.path.exists(vendor_defaults_file):
            with open(vendor_defaults_file, 'r') as f:
                vendor_defaults = yaml.load(f)
                self._data = vendor_defaults.copy()
        else:
            logger.warning("Vendor Customs Defaults File Not Found : " + vendor_defaults_file)
        self._source_folder = os.path.split(inv_yaml)[0]
        with open(inv_yaml, 'r') as f:
            inv_data = yaml.load(f)
            self._data.update(inv_data)
        self._linetype = CustomsInvoiceLine
        super(CustomsInvoice, self).__init__(vendor, self._data['invoice_no'], self._data['invoice_date'])
        self.freight = 0
        self.insurance_pc = 0
        self._process_other_costs()
        hs_codes_file = os.path.join(CUSTOMSDEFAULTS_FOLDER, 'hs_codes.yaml')
        with open(hs_codes_file, 'r') as f:
            self._hs_codes = yaml.load(f)
        self._sections = []
        self._classify()

    def _process_other_costs(self):
        for k, v in self._data['costs_not_included'].iteritems():
            if v is False:
                self._data['costs_not_included'][k] = 'None'
            elif v == 'INCL':
                self._data['costs_not_included'][k] = 'None, included in Invoice'
            else:
                logger.warning("Unrecognized Other Costs definition for " + k + " : " + v)
        if self._data['costs_not_included']['FREIGHT'] == 'None, included in Invoice':
            self.freight = utils.currency.CurrencyValue(float(self._data['shipping_cost_incl']),
                                                         self._vendor.currency)
            self._data['costs_not_included']['FREIGHT'] += " ({0})".format(self.freight.source_string)
        if 'insurance_pc' in self._data.keys():
            self.insurance_pc = float(self._data['insurance_pc'])

    @property
    def source_folder(self):
        return self._source_folder

    @property
    def idxs(self):
        return [x.idx for x in self._lines]

    def _acquire_lines(self):
        raise NotImplementedError

    @property
    def hssections(self):
        rval = []
        for line in self._lines:
            if line.hs_section is None:
                continue
            if line.hs_section not in rval:
                rval.append(line.hs_section)
        return sorted(rval, key=lambda x: x.code)

    def getsectionlines(self, hssection):
        rval = []
        for line in self._lines:
            if line.hs_section == hssection:
                rval.append(line)
        return rval

    @property
    def unclassified(self):
        rval = []
        for line in self._lines:
            if line.hs_section is None:
                rval.append(line)
        return rval

    @property
    def assessabletotal(self):
        return sum([x.assessableprice for x in self._lines])

    def _classify(self):
        logger.info("Attempting to classify")
        pass


class CustomsInvoiceLine(vendors.VendorInvoiceLine):
    def __init__(self, invoice, ident, vpno, unitp, qty, idx=None, desc=None):
        if idx is None:
            idx = max(invoice.idxs) + 1
        super(CustomsInvoiceLine, self).__init__(invoice, ident, vpno, unitp, qty, desc=desc)
        if idx in invoice.idxs:
            raise ValueError
        self._idx = idx

    @property
    def assessableprice(self):
        rval = self.extendedprice
        if self._invoice.freight is not None:
            rval += self._invoice.freight * (self.extendedprice / self._invoice.extendedtotal)
        if self._invoice.insurance_pc is not None:
            rval += self.extendedprice * (self._invoice.insurance_pc / 100)
        return rval

    @property
    def idx(self):
        return self._idx

    @property
    def hs_section(self):
        try:
            hs_section = hs_classifier.hs_from_ident(self.ident)
        except ValueError:
            hs_section = None

        if hs_section is None:
            logger.warning("Could not classify : " + self.ident)
        return hs_section

    def __repr__(self):
        if self.hs_section is not None:
            return "{0:<3} {1:<40} {2:<35} {3:>10} {4:>15}".format(self.idx, self._ident, self._desc, self.hs_section.code, self.hs_section.name)
        else:
            return "{0:<3} {1:<40} {2:<35} {3:>10} {4:>15}".format(self.idx, self._ident, self._desc, '----------', 'Unclassified')
