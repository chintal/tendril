"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""

import jinja2

import inspect
import os
import subprocess

template_folder = os.path.normpath(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))) + '/../dox/templates')


def jinja2_pdfinit():
    loader = jinja2.FileSystemLoader(template_folder)
    renderer = jinja2.Environment(block_start_string='%{',
                                  block_end_string='%}',
                                  variable_start_string='%{{',
                                  variable_end_string='%}}',
                                  loader=loader)
    return renderer

renderer_pdf = jinja2_pdfinit()


def render_pdf(stage, template, outpath):

    template = renderer_pdf.get_template(template)

    stage['logo'] = os.path.normpath(template_folder + "/graphics/logo.png")
    stage['company'] = 'Quazar Technologies Pvt Ltd'
    texpath = os.path.splitext(outpath)[0] + ".tex"
    with open(texpath, "wb") as f:
        f.write(template.render(stage=stage))

    texpath = os.path.splitext(outpath)[0] + ".tex"
    auxpath = os.path.splitext(outpath)[0] + ".aux"
    logpath = os.path.splitext(outpath)[0] + ".log"

    pdflatex_cmd = ("pdflatex --output-directory=" + os.path.split(outpath)[0]).split(' ')
    pdflatex_cmd.append(texpath)

    for i in range(3):
        subprocess.call(pdflatex_cmd)

    os.remove(texpath)
    os.remove(auxpath)
    os.remove(logpath)

    return outpath
