"""
Dox Render module documentation (:mod:`dox.render`)
===================================================
"""


import jinja2

import os
import subprocess

from utils.config import DOX_TEMPLATE_FOLDER
from utils.config import COMPANY_LOGO_PATH
from utils.config import COMPANY_NAME


def jinja2_pdfinit():
    loader = jinja2.FileSystemLoader(DOX_TEMPLATE_FOLDER)
    renderer = jinja2.Environment(block_start_string='%{',
                                  block_end_string='%}',
                                  variable_start_string='%{{',
                                  variable_end_string='%}}',
                                  loader=loader)
    return renderer

renderer_pdf = jinja2_pdfinit()


def render_pdf(stage, template, outpath):

    template = renderer_pdf.get_template(template)

    stage['logo'] = COMPANY_LOGO_PATH
    stage['company'] = COMPANY_NAME
    texpath = os.path.splitext(outpath)[0] + ".tex"
    with open(texpath, "wb") as f:
        f.write(template.render(stage=stage))

    texpath = os.path.splitext(outpath)[0] + ".tex"
    auxpath = os.path.splitext(outpath)[0] + ".aux"
    logpath = os.path.splitext(outpath)[0] + ".log"

    pdflatex_cmd = ("pdflatex -interaction=batchmode -output-directory=" + os.path.split(outpath)[0]).split(' ')
    pdflatex_cmd.append(texpath)

    for i in range(3):
        subprocess.call(pdflatex_cmd)

    os.remove(texpath)
    os.remove(auxpath)
    os.remove(logpath)

    return outpath
