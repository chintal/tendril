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
Purchase Orders Dox Module (:mod:`tendril.dox.purchaseorder`)
=============================================================

This module provides functions to generate purchase orders.

The underlying assumption made in this module is that Purchase Orders are
relatively specific to vendors and include information that may be specific
to the materials being purchased. While this approach does need streamlining,
for the moment this works well enough to be functional.

.. todo:: Streamline the approach and the stage format.

The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

.. seealso:: :mod:`tendril.dox`

.. rubric:: Document Generators

.. autosummary::

    render_po

"""

import datetime

import render
from tendril.entityhub import serialnos

from tendril.utils.config import COMPANY_PO_LCO_PATH
from tendril.utils.config import COMPANY_PO_POINT


def render_po(stage, templateid, outpath):
    """
    Generates a purchase order using the template indicated by ``templateid``.

    :param stage: The dictionary to be sent along to the jinja2 template.
    :type stage: dict
    :param templateid: The id of the template to use.
    :type templateid: str
    :param outpath: The path to which the output should be written,
                    including ``.pdf``.
    :type outpath: str
    :return: The ``outpath``.

    .. rubric:: Template Used

    This function uses a template specified by ``templateid``, specifically,
    using the template named ``po_[templateid]_template.tex``.

    .. rubric:: Stage Keys Provided

    The contents of the ``stage`` provided to the jinja2 template are specific
    to each template, and it is the responsibility of the caller to make sure
    that it contains all the keys that the template expects. The parts of the
    stage defined by this function, common to all templates, are :

    .. list-table::

        * - ``no``
          - The serial number of the purchase order, either from the ``stage``
            parameter or created.
        * - ``point``
          - The name of the contact person, defined by
            :data:`tendril.utils.config.COMPANY_PO_POINT`.
        * - ``date``
          - The purchase order date, either from the ``stage`` parameter or
            today's date.
        * - ``lcofile``
          - The latex lcofile to use, defined by
            :data:`tendril.utils.config.COMPANY_PO_LCO_PATH`

    """
    template = 'po_' + templateid + '_template.tex'
    stage['lcofile'] = COMPANY_PO_LCO_PATH
    if 'point' not in stage.keys():
        stage['point'] = COMPANY_PO_POINT
    if 'no' not in stage.keys():
        stage['no'] = serialnos.get_serialno(series='PO', efield=templateid)
    if 'date' not in stage.keys():
        stage['date'] = str(datetime.date.today())
    return render.render_pdf(stage, template, outpath)
