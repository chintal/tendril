"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import datetime

import render
from entityhub.serialnos import last_serial

from utils.config import COMPANY_PO_LCO_PATH
from utils.config import COMPANY_PO_POINT


def render_po(stage, templateid, outpath):
    template = 'po_' + templateid + '_template.tex'
    stage['lcofile'] = COMPANY_PO_LCO_PATH
    if 'point' not in stage.keys():
        stage['point'] = COMPANY_PO_POINT
    if 'no' not in stage.keys():
        stage['no'] = 'PO/2015-16/' + "%03d" % (last_serial['dox']['po'] + 1)
        last_serial['dox']['po'] += 1
    if 'date' not in stage.keys():
        stage['date'] = str(datetime.date.today())
    return render.render_pdf(stage, template, outpath)
