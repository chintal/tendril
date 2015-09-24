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
Core Dox Render Module (:mod:`tendril.dox.render`)
==================================================

This module provides the underlying rendering functions to produce PDF
output. Other :mod:`tendril.dox` modules should use these functions to
generate their output files.


.. rubric:: Processors

.. autosummary::

    format_currency
    escape_latex
    jinja2_pdfinit

.. rubric:: Renderers

.. autosummary::

    render_pdf
    render_lineplot
    make_graph
    make_histogram

"""

import os
import subprocess
import jinja2

import numpy
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

from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)


def format_currency(value):
    """
    Formats a number into the correct number of decimals (2) and with
    thousands separators ``,``, for use when rendering currencies.

    This function is added to the :mod:`jinja2` PDF environment constructed by
    :func:`jinja2_pdfinit`, and is available as a filter in jinja2 templates.

    :type value: float
    :rtype: str

    """
    return "{:,.2f}".format(value)


def escape_latex(string, aggressive=True):
    """
    Escapes latex control and reserved characters from the string. It also
    converts `None` type inputs into an empty string.

    This is also where 'special' string sequences are defined to produce
    specialized latex output, such as the conversion of ``INR`` to the
    rupee symbol, via the latex ``\\rupee~`` command provided by ``tfrupee``.

    :param string: Input string
    :return: Latex-safe string

    """
    if string is not None:
        string = string.replace('\\', '\\\\')
        string = string.replace('$', '\$')
        string = string.replace('%', '\%')
        string = string.replace('&', '\&')
        string = string.replace('_', '\_')
        string = string.replace('INR ', '\\rupee~')
        if aggressive is True:
            string = string.replace('--', '-{}-')
    else:
        string = ''
    return string


def jinja2_pdfinit():
    """
    Creates a :class:`jinja2.Environment`, stored in this module's
    :data:`renderer_pdf` variable.

    Application code would typically not call this function or interact
    directly wih the renderer, and instead use the various render
    functions provided in this module. If the renderer is required, the
    instance at :data:`tendril.dox.render.renderer_pdf` can be used.

    .. rubric:: Environment Information

    The environment created here is optimised to produce latex output.

    .. rubric:: Loader

    :class:`jinja2.FileSystemLoader`, with it's root at
    :data:`tendril.utils.config.DOX_TEMPLATE_FOLDER`

    .. rubric:: Template Markup Strings

    - Blocks:      ``%{      %}``
    - Variables:   ``%{{    %}}``
    - Comments:    ``%{#    %#}``

    .. rubric:: Filters

    - :func:`format_currency`
    - :func:`escape_latex`

    :return: The jinja2 Environment.

    """
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

#: The jinja2 environment which application code
#: can use to produce latex output.
renderer_pdf = jinja2_pdfinit()


def render_pdf(stage, template, outpath, remove_sources=True, **kwargs):
    """
    Render the latex output and convert it into pdf using ``pdflatex``.

    The ``stage`` is a dictionary passed on to the :mod:`jinja2`
    environment, as is available within the template. This function adds
    some common variables to the ``stage``.

    This function makes three ``pdflatex`` passes to make sure all the
    references are resolved.

    This function will remove the sources, i.e., the ``.tex`` files and
    intermediate files produced by ``pdflatex``, after conversion. It will
    do so after running ``pdflatex``, irrespective of the result. If the
    raw ``.tex`` file is needed (typically for debugging templates), the
    ``remove_sources`` parameter should be used.

    :param stage: A dictionary which will be available to the template
    :type stage: dict
    :param template: The template file to use, either relative to the
                     loader's template root or an absolute path.
    :type template: str
    :param outpath: The path to the output file (including ``.pdf``).
    :type outpath: str
    :param remove_sources: Whether to remove the latex files after conversion.
    :type remove_sources: bool
    :return: ``outpath``

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``logo``
          - The company logo, as specified in
            :data:`tendril.utils.config.COMPANY_LOGO_PATH`
        * - ``company``
          - The company name, as specified in
            :data:`tendril.utils.config.COMPANY_NAME`
        * - ``company_email``
          - The company email address, as specified in
            :data:`tendril.utils.config.COMPANY_EMAIL`
        * - ``company_address_line``
          - The company address, as specified in
            :data:`tendril.utils.config.COMPANY_ADDRESS_LINE`
        * - ``company_iec``
          - The company IEC, as specified in
            :data:`tendril.utils.config.COMPANY_IEC`

    """
    if not os.path.exists(template) \
            and not os.path.exists(
                os.path.join(DOX_TEMPLATE_FOLDER, template)
            ):
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

    pdflatex_cmd = ("pdflatex -interaction=batchmode -output-directory=" +
                    os.path.split(outpath)[0]).split(' ')
    pdflatex_cmd.append(texpath)

    for i in range(3):
        subprocess.call(pdflatex_cmd)

    if remove_sources is True:
        os.remove(texpath)
        os.remove(auxpath)
        os.remove(logpath)

    return outpath


def render_lineplot(outf, plotdata, title, note):
    """
    Renders a lineplot to PDF. This function is presently used to generate
    PCB pricing graphs by :mod:`tendril.dox.gedaproject.gen_pcbpricing`.
    It's pretty unwieldy, and is likely going to be axed at some point in
    favor of :func:`make_graph`, once the necessary functionality is
    implemented there and the pricing graph code is modified to use that
    instead.

    .. warning:: This function is likely to be deprecated.
    .. seealso:: :func:`make_graph`

    :param outf: The path to the output file.
    :param plotdata: The data to plot.
    :param title: The title of the plot.
    :param note: An additional note to include with the plot (not implemented)
    :return: outf
    """

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

    pl.yticks(range(0, int(ymax), int(ymax / 10)),
              [str(x) for x in range(0, int(ymax), int(ymax / 10))])

    for y in range(0, int(ymax), int(ymax / 10)):
        ax.plot(range(xmin, xmax), [y] * len(range(xmin, xmax)),
                "--", lw=0.5, color="black", alpha=0.3)

    pl.tick_params(axis="both", which="both", bottom="off", top="off",
                   labelbottom="on", left="off", right="off", labelleft="on")

    pl.ylim(0, ymax)
    pl.xlim(xmin, xmax)

    for idx, curvename in enumerate(curvenames):
        ax.plot(xlists[idx], ylists[idx],
                color=tableau20[idx], label=curvename)
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
               xlabel='', ylabel='', ymax=None, ymin=None):
    """
    Renders a graph of the data provided as a ``.png`` file, saved to the
    path specified by ``outpath``. This function uses :mod:`matplotlib.pyplot`.

    :param outpath: The path to the output file
    :type outpath: str
    :param plotdata_y: The y-axis data to plot
    :type plotdata_y: list
    :param plotdata_x: The x-axis data to plot, or None if
                       a plotdata_y is a sequence
    :type plotdata_x: :class:`list` or None
    :param color: The color of the curve, default ``black``.
                  See matplotlib docs.
    :type color: str
    :param lw: The linewidth of the curve, default ``2``.
               See matplotlib docs.
    :type lw: int
    :param marker: The marker to be used, default ``None``.
                   See matplotlib docs.
    :type marker: str
    :param xscale: The scale of the x axis, default ``linear``.
                   See matplotlib docs.
    :type xscale: str
    :param yscale: The scale of the y axis, default ``linear``.
                   See matplotlib docs.
    :type yscale: str
    :param xlabel: The x-axis label, default ``''``
    :type xlabel: str
    :param ylabel: The y-axis label, default ``''``
    :type ylabel: str
    :return: The output path.
    """
    pyplot.plot(plotdata_x, plotdata_y,
                color=color, lw=lw, marker=marker)
    pyplot.xscale(xscale)
    pyplot.yscale(yscale)
    pyplot.grid(True, which='major', color='0.3', linestyle='-')
    pyplot.grid(True, which='minor', color='0.3')
    pyplot.xlabel(xlabel, fontsize=20)
    pyplot.ylabel(ylabel, fontsize=20)
    pyplot.tick_params(axis='both', which='major', labelsize=16)
    pyplot.tick_params(axis='both', which='minor', labelsize=8)
    if (ymax, ymin) is not (None, None):
        pyplot.ylim((ymin, ymax))
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

    .. warning:: This function fails if the provided data lacks a proper
                 distribution, such as if there are only 4 distinct values
                 in the output. Figure out why and how to fix it. In the
                 meanwhile, specify bins manually to not let this function
                 be called.
    """

    max_p = max(plotdata_y)
    min_p = min(plotdata_y)

    n_min = 2
    n_max = 50
    n = range(n_min, n_max)

    # Number of Bins array
    n = numpy.array(n)
    # Bin Size Vector
    d = (max_p - min_p) / n

    c = numpy.zeros(shape=(numpy.size(d), 1))

    # Computation of the cost function
    for i in xrange(numpy.size(n)):
        edges = numpy.linspace(min_p, max_p, n[i]+1)  # Bin edges
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
    """
    Renders a histogram of the data provided as a ``.png`` file,
    saved to the path specified by ``outpath``.
    This function uses :mod:`matplotlib.pyplot`.

    .. seealso:: :func:`get_optimum_bins`

    :param outpath: The path to the output file
    :type outpath: str
    :param plotdata_y: The y-axis data to plot
    :type plotdata_y: list
    :param bins: Number of bins to use. If None, uses the optimum.
                 See matplotlib docs.
    :type bins: int or None
    :param color: The color of the curve, default ``red``.
                  See matplotlib docs.
    :type color: str
    :param xlabel: The x-axis label, default ``''``
    :type xlabel: str
    :param ylabel: The y-axis label, default ``''``
    :type ylabel: str
    :param x_range: The x-axis range, if not the default.
                    See matplotlib docs for range.
    :type x_range: tuple
    :return: The output path.
    """
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
