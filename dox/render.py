"""
Dox Render module documentation (:mod:`dox.render`)
===================================================
"""

import os
import subprocess
import re

import jinja2
import matplotlib
matplotlib.use('PDF')

from utils.config import DOX_TEMPLATE_FOLDER
from utils.config import COMPANY_LOGO_PATH
from utils.config import COMPANY_NAME
from utils.config import COMPANY_ADDRESS_LINE

from utils.colors import tableau20


def format_currency(value):
    return "{:,.2f}".format(value)


def escape_latex(string):
    if string is not None:
        string = string.replace('\\', '\\\\')
        string = string.replace('$', '\$')
        string = string.replace('%', '\%')
        string = string.replace('&', '\&')
        string = string.replace('_', '\_')
        string = string.replace('INR ', '\\rupee~')
    else:
        string = ''
    return string


def jinja2_pdfinit():
    loader = jinja2.FileSystemLoader(DOX_TEMPLATE_FOLDER)
    renderer = jinja2.Environment(block_start_string='%{',
                                  block_end_string='%}',
                                  variable_start_string='%{{',
                                  variable_end_string='%}}',
                                  loader=loader)
    renderer.filters['format_currency'] = format_currency
    renderer.filters['escape_latex'] = escape_latex
    return renderer

renderer_pdf = jinja2_pdfinit()


def render_pdf(stage, template, outpath, remove_sources=True, **kwargs):

    template = renderer_pdf.get_template(template)

    stage['logo'] = COMPANY_LOGO_PATH
    stage['company'] = COMPANY_NAME
    stage['company_address_line'] = COMPANY_ADDRESS_LINE
    texpath = os.path.splitext(outpath)[0] + ".tex"
    with open(texpath, "wb") as f:
        f.write(template.render(stage=stage, **kwargs))

    texpath = os.path.splitext(outpath)[0] + ".tex"
    auxpath = os.path.splitext(outpath)[0] + ".aux"
    logpath = os.path.splitext(outpath)[0] + ".log"

    pdflatex_cmd = ("pdflatex -interaction=batchmode -output-directory=" + os.path.split(outpath)[0]).split(' ')
    pdflatex_cmd.append(texpath)

    for i in range(3):
        subprocess.call(pdflatex_cmd)

    if remove_sources is True:
        os.remove(texpath)
        os.remove(auxpath)
        os.remove(logpath)

    return outpath


def render_lineplot(outf, plotdata, title, note):
    curvenames = []
    ylists = []
    xlists = []
    for x, y in plotdata.iteritems():
        for name, value in y.iteritems():
            if name not in curvenames:
                curvenames.append(name)
                xlists.append([])
                ylists.append([])
            curveindex = curvenames.index(name)
            xlists[curveindex].append(x)
            ylists[curveindex].append(value)

    import matplotlib.pylab as pl
    pl.figure(1, figsize=(11.69, 8.27))
    ax = pl.subplot(111)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    try:
        ymax = max([max(l) for l in ylists])
    except ValueError:
        print ylists
        raise ValueError
    xmin = min([min(l) for l in xlists])
    xmax = max([max(l) for l in xlists])

    pl.yticks(range(0, int(ymax), int(ymax/10)), [str(x) for x in range(0, int(ymax), int(ymax/10))])

    for y in range(0, int(ymax), int(ymax/10)):
        ax.plot(range(xmin, xmax), [y] * len(range(xmin, xmax)), "--", lw=0.5, color="black", alpha=0.3)

    pl.tick_params(axis="both", which="both", bottom="off", top="off",
                   labelbottom="on", left="off", right="off", labelleft="on")

    pl.ylim(0, ymax)
    pl.xlim(xmin, xmax)

    for idx, curvename in enumerate(curvenames):
        ax.plot(xlists[idx], ylists[idx], color=tableau20[idx], label=curvename)
        # y_pos = ylists[idx][-1] - 0.5
        # pl.text(xmax, y_pos, curvename, color=tableau20[idx])
    pl.title(title)

    pl.legend()
    pl.savefig(outf, format='pdf')
    pl.clf()
    return outf
