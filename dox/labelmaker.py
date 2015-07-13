"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

import os
import qrcode

import render
from utils.fs import TEMPDIR
from utils.config import COMPANY_NAME
from utils.config import COMPANY_LOGO_PATH

LABEL_TEMPLATES_ROOT = 'labels'


class LabelBase(object):

    templatefile = None

    def __init__(self, code, ident, sno, branding=None, logo=None):
        self._code = code
        self._sno = sno
        self._ident = ident
        if branding is None:
            self._branding = COMPANY_NAME
        else:
            self._branding = branding
        if logo is None:
            self._logo = COMPANY_LOGO_PATH
        else:
            self._logo = logo
        self._include_qr = True
        self._include_logo = True
        self._qr_path = None
        if self._include_qr is True:
            self._gen_qrcode()

    @property
    def code(self):
        return self._code

    @property
    def sno(self):
        return self._sno

    @property
    def ident(self):
        # if len(self._ident) > 16:
        #     return r"\tiny " + self._ident
        # if len(self._ident) > 14:
        #     return r"\scriptsize " + self._ident
        # else:
        return r"\footnotesize " + self._ident

    @property
    def branding(self):
        return self._branding

    @property
    def include_logo(self):
        return self._include_logo

    @property
    def include_qr(self):
        return self._include_qr

    @property
    def logo(self):
        return self._logo

    @property
    def qrcode(self):
        return self._qr_path

    def _gen_qrcode(self, wfpath=None):
        if wfpath is None:
            wfpath = TEMPDIR
        qr = qrcode.make(self._ident + ' ' + self._sno)
        self._qr_path = os.path.join(wfpath, 'QR-' + self._ident + '-' + self._sno + '.png')
        qr.save(self._qr_path)

    def __repr__(self):
        return "<Label for " + self._ident + ' ' + self._sno + '>'


class LabelCW1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')

class LabelP1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')

class LabelP2(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')

class LabelD1(LabelBase):
    templatefile = os.path.join(LABEL_TEMPLATES_ROOT, 'CW1_template.tex')


def get_labelbase(code):
    # TODO change this dispatch to use introspection instead
    if code == 'CW1':
        return LabelCW1
    elif code == 'D1':
        return LabelD1
    elif code == 'P1':
        return LabelP1
    elif code == 'P2':
        return LabelP2
    else:
        return LabelBase


class LabelSheet(object):
    def __init__(self, base, code):
        self._base = base
        self._code = code
        self._labels = []

    @property
    def code(self):
        return self._code

    @property
    def base(self):
        return self._base

    @property
    def labels(self):
        for label in self._labels:
            yield label

    def add_label(self, label):
        self._labels.append(label)

    def generate_pdf(self, targetfolder):
        stage = {'labels': self._labels}
        return render.render_pdf(stage, self._base.templatefile,
                                 os.path.join(targetfolder, 'labels-' + self.code + '.pdf'))


class LabelMaker(object):
    def __init__(self):
        self._sheets = []

    def add_label(self, code, ident, sno):
        sheet = self._get_sheet(code)
        label = sheet.base(code, ident, sno)
        sheet.add_label(label)

    def _get_sheet(self, code):
        if code not in self._sheetdict.keys():
            self._sheets.append(LabelSheet(get_labelbase(code), code))
        return self._sheetdict[code]

    @property
    def _sheetdict(self):
        return {x.code: x for x in self._sheets}

    def generate_pdfs(self, targetfolder):
        rval = []
        for sheet in self._sheets:
            rval.append(sheet.generate_pdf(targetfolder))
        return rval

manager = LabelMaker()
