# coding=utf-8
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
Dox Render module documentation (:mod:`dox.render`)
===================================================
"""

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

import os
import subprocess
import jinja2

import numpy
from scipy import linspace

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot

from tendril.utils.config import DOX_TEMPLATE_FOLDER
from tendril.utils.config import COMPANY_LOGO_PATH
from tendril.utils.config import COMPANY_NAME
from tendril.utils.config import COMPANY_EMAIL
from tendril.utils.config import COMPANY_ADDRESS_LINE
from tendril.utils.config import COMPANY_IEC

from tendril.utils.colors import tableau20


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
                                  comment_start_string='%{#',
                                  comment_end_string='%#}',
                                  loader=loader)
    renderer.filters['format_currency'] = format_currency
    renderer.filters['escape_latex'] = escape_latex
    return renderer

renderer_pdf = jinja2_pdfinit()


def render_pdf(stage, template, outpath, remove_sources=True, **kwargs):
    if not os.path.exists(template) and not os.path.exists(os.path.join(DOX_TEMPLATE_FOLDER, template)):
        logger.error("Template not found : " + template)
        raise ValueError
    template = renderer_pdf.get_template(template)

    stage['logo'] = COMPANY_LOGO_PATH
    stage['company'] = COMPANY_NAME
    stage['company_email'] = COMPANY_EMAIL
    stage['company_address_line'] = COMPANY_ADDRESS_LINE
    stage['company_iec'] = COMPANY_IEC
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
    # Deprecated ?
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

    pl.yticks(range(0, int(ymax), int(ymax / 10)), [str(x) for x in range(0, int(ymax), int(ymax / 10))])

    for y in range(0, int(ymax), int(ymax / 10)):
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


def make_graph(outpath, plotdata_y, plotdata_x=None,
               color='black', lw=2, marker=None,
               xscale='linear', yscale='linear',
               xlabel='', ylabel=''):
    pyplot.plot(plotdata_x, plotdata_y, color=color, lw=lw, marker=marker)
    pyplot.xscale(xscale)
    pyplot.yscale(yscale)
    pyplot.grid(True, which='major', color='0.3', linestyle='-')
    pyplot.grid(True, which='minor', color='0.3')
    pyplot.xlabel(xlabel, fontsize=20)
    pyplot.ylabel(ylabel, fontsize=20)
    pyplot.tick_params(axis='both', which='major', labelsize=16)
    pyplot.tick_params(axis='both', which='minor', labelsize=8)
    pyplot.tight_layout()
    pyplot.savefig(outpath)
    pyplot.close()
    return outpath


def get_optimum_bins(plotdata_y):
    """
    Histogram Binwidth Optimization Method

    ::

        Shimazaki and Shinomoto, Neural Comput 19 1503-1527, 2007
        2006 Author Hideaki Shimazaki, Matlab
        Department of Physics, Kyoto University
        shimazaki at ton.scphys.kyoto-u.ac.jp

    This implementation based on the version in python
    written by Érbet Almeida Costa

    :param plotdata_y: The data for which a histogram is to be made
    :return: The optimal number of bins
    """

    max_p = max(plotdata_y)
    min_p = min(plotdata_y)
    n_min = 4
    n_max = 50
    n = range(n_min, n_max)

    # Number of Bins array
    n = numpy.array(n)
    # Bin Size Vector
    d = (max_p - min_p) / n

    c = numpy.zeros(shape=(numpy.size(d), 1))

    # Computation of the cost function
    for i in xrange(numpy.size(n)):
        edges = linspace(min_p, max_p, n[i]+1)  # Bin edges
        ki = pyplot.hist(plotdata_y, edges)     # Count # of events in bins
        ki = ki[0]
        k = numpy.mean(ki)                      # Mean of event count
        v = sum((ki - k) ** 2) / n[i]           # Variance of event count
        c[i] = (2 * k - v) / ((d[i]) ** 2)      # The cost Function

    # Optimal Bin Size Selection
    cmin = min(c)
    idx = numpy.where(c == cmin)
    idx = int(idx[0])
    pyplot.close()
    return n[idx]


def make_histogram(outpath, plotdata_y, bins=None, color='red',
                   xlabel='', ylabel='', x_range=None):
    if bins is None:
        bins = get_optimum_bins(plotdata_y)
    pyplot.hist(plotdata_y, bins=bins, color=color, range=x_range)
    pyplot.grid(True, which='major', linestyle='-')
    pyplot.grid(True, which='minor')
    pyplot.xlabel(xlabel, fontsize=20)
    pyplot.ylabel(ylabel, fontsize=20)
    pyplot.tick_params(axis='both', which='major', labelsize=16)
    pyplot.tick_params(axis='both', which='minor', labelsize=8)
    pyplot.tight_layout()
    pyplot.savefig(outpath)
    pyplot.close()
    return outpath

