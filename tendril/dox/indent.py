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
Indent Dox Module (:mod:`tendril.dox.indent`)
=============================================

This module provides functions to generate stock / inventory indents.

The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

.. seealso:: :mod:`tendril.dox`

.. rubric:: Document Generators

.. autosummary::

    gen_stock_idt_from_cobom


"""

import render
import os

import labelmaker


def gen_stock_idt_from_cobom(outfolder, sno, title, carddict, cobom):
    """
    Generates a stock indent from a
    :class:`tendril.boms.outputbase.CompositeOutputBom` instance. This
    function also adds ``IDT`` labels for all the stock / inventory items that
    are requested for by the indent to the
    :data:`tendril.dox.labelmaker.manager`, though the caller should make sure
    that the labels are written out after the fact.

    .. note::
        This function does not register the document in the
        :mod:`tendril.dox.docstore`. You should use the output file path
        (returned by this function) to register the document when desired.

    :param outfolder: The folder within which the output PDF should
                      be created.
    :type outfolder: str
    :param sno: The serial number of the Indent
    :type sno: str
    :param title: The title of the Indent
    :param carddict: A dictionary containing the list of card types included
                     for the indent (keys) and the quantity for each (values).
    :type carddict: dict
    :param cobom: The composite output BOM, including the BOMs for the cards
                  that the indent is being constructed for.
    :type cobom: :class:`tendril.boms.outputbase.CompositeOutputBom`
    :return: The output file path.

    .. rubric:: Template Used

    ``tendril\dox\\templates\indent_stock_template.tex``
    (:download:`Included version
    <../../tendril/dox/templates/indent_stock_template.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``sno``
          - The serial number of the indent.
        * - ``title``
          - Whether the device is a PCB or a Cable.
        * - ``lines``
          - List of dictionaries, each containing the ``ident`` and ``qty``
            of one line in the indent.
        * - ``cards``
          - A string listing out the various cards the indent was generated
            to request components for.

    """
    outpath = os.path.join(outfolder, str(sno) + '.pdf')
    cards = ""
    for card, qty in sorted(carddict.iteritems()):
        cards += card + ' x' + str(qty) + ', '

    indentsno = sno

    lines = []
    for idx, line in enumerate(cobom.lines):
        lines.append({'ident': line.ident, 'qty': line.quantity})
        labelmaker.manager.add_label(
            'IDT', line.ident, indentsno + '.' + str(idx), qty=line.quantity)

    stage = {'title': title,
             'sno': indentsno,
             'lines': lines,
             'cards': cards}

    template = 'indent_stock_template.tex'
    render.render_pdf(stage, template, outpath)

    return outpath, indentsno