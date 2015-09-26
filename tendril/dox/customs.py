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
Customs Dox Module (:mod:`tendril.dox.customs`)
===============================================

This module generates the customs document sets.

The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

.. hint:: The functions and templates here are made for and in the Indian
          Customs formats. This probably doesn't translate well to any other
          country. As such, this module itself doesn't do much of the heavy
          lifting. Instead, it relies on the :mod:`tendril.sourcing.customs`
          module. Porting it to another country would probably start from
          reimplementing that class and rewriting the templates.

.. seealso:: :mod:`tendril.dox`, :mod:`tendril.sourcing.customs`

.. rubric:: Document Set Generators

.. autosummary::

    generate_docs
    gen_submitdocs
    gen_verificationdocs

.. rubric:: Document Generators

.. autosummary::

    gen_declaration
    gen_valuation
    gen_rsp_declaration
    gen_authorization
    gen_tech_writeup
    gen_verification_sections
    gen_verification_checklist

"""

import os
import datetime
import copy
import yaml
import fs

import render
import wallet
import docstore

from tendril.utils import pdf
from tendril.utils.db import with_db
from tendril.entityhub import serialnos
from tendril.utils.fsutils import get_tempname
from tendril.utils.fsutils import temp_fs

from tendril.utils.config import COMPANY_GOVT_POINT


def gen_declaration(invoice, target_folder, copyt, serialno):
    """
    Generates a copy of the Customs Declaration for Imports.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param copyt: A string specifying which copy it is ("ORIGINAL",
                  "DUPLICATE", so on)
    :type copyt: str
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file path

    .. rubric:: Template Used

    ``tendril/dox/templates/customs/decl.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/decl.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at, from
            :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`
        * - ``currency``
          - The symbol of the currency of the invoice.
        * - ``inv_total``
          - The total value of the invoice, in vendor currency.
        * - ``exchrate``
          - The applicable exchange rate.
        * - ``exchnotif``
          - The government notification number specifying the exchange rate.
        * - ``exchnotifdt``
          - The date of the exchange rate notification.
        * - ``extended_total_sc``
          - The extended total invoice value, in the vendor's currency.
        * - ``assessable_total_sc``
          - The assessable total invoice value, in the vendor's currency.
        * - ``assessable_total_nc``
          - The assessable total invoice value, in the vendor's currency.
        * - ``copyt``
          - The string specifying which copy it is.
        * - ``sno``
          - The serial number of the document.

    """
    outpath = os.path.join(
        target_folder,
        "customs-declaration-" + copyt + '-' + str(invoice.inv_no) + ".pdf"
    )

    given_data = copy.deepcopy(invoice.given_data)

    for k, v in given_data['costs_not_included'].iteritems():
        given_data['costs_not_included'][k] = render.escape_latex(v)

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': given_data,
             'currency': render.escape_latex(invoice.currency.symbol),
             'inv_total':
             render.escape_latex(invoice.extendedtotal.source_string),
             'exchrate': invoice.given_data['exchrate'],
             'exchnotif': invoice.given_data['exchnotif'],
             'exchnotifdt': invoice.given_data['exchnotif_date'],
             'extended_total_sc':
             render.escape_latex(invoice.extendedtotal.source_string),
             'assessable_total_sc':
             render.escape_latex(invoice.assessabletotal.source_string),
             'assessable_total_nc':
             render.escape_latex(invoice.assessabletotal.native_string),
             'copyt': copyt,
             'sno': serialno + '.5'
             }

    return render.render_pdf(stage, 'customs/decl.tex', outpath)


def gen_valuation(invoice, target_folder, serialno):
    """
    Generates the Customs Valuation Note.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file path

    .. rubric:: Template Used

    ``tendril/dox/templates/customs/valuation.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/valuation.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at, from
            :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`
        * - ``currency``
          - The symbol of the currency of the invoice.
        * - ``inv_total``
          - The total value of the invoice, in vendor currency.
        * - ``exchrate``
          - The applicable exchange rate.
        * - ``exchnotif``
          - The government notification number specifying the exchange rate.
        * - ``exchnotifdt``
          - The date of the exchange rate notification.
        * - ``note1``
          - A note mentioning the inclusion of freight.
        * - ``note2``
          - A list of strings mentioning other additions to the valuation.
        * - ``include_note2``
          - Boolean, whether or not to include note2.
        * - ``extended_total_sc``
          - The extended total invoice value, in the vendor's currency.
        * - ``assessable_total_sc``
          - The assessable total invoice value, in the vendor's currency.
        * - ``assessable_total_nc``
          - The assessable total invoice value, in the vendor's currency.
        * - ``copyt``
          - The string specifying which copy it is.
        * - ``sno``
          - The serial number of the document.
        * - ``is_wire``
          - Bool, whether the payment was made by a wire transfer.

    """
    outpath = os.path.join(
        target_folder,
        "customs-valuation-" + str(invoice.inv_no) + ".pdf"
    )

    note1 = ''
    if invoice.includes_freight is True:
        note1 += "As listed in the invoice, {0} towards freight " \
                 "is also added. ".format(invoice.freight.source_string)
    note1 = render.escape_latex(note1)

    note2 = []

    if invoice.added_insurance is True:
        note2.append(
            "An additional {0}% of FOB is added to the assessable value "
            "as per Rule 10(2)(c)(iii) of Customs Valuation "
            "(Determination of Value of Imported Goods) Rules, 2007. "
            "No specific insurance charges were paid as part of the"
            " transaction.".format(invoice.insurance_pc)
        )
    if invoice.added_handling is True:
        note2.append(
            "An additional {0}% of CIF is added to the assessable value "
            "as per Rule 10(2)(b)(ii) of Customs Valuation "
            "(Determination of Value of Imported Goods) Rules, 2007. "
            "No specific handling charges were paid as part of the"
            " transaction.".format(invoice.handling_pc)
        )

    include_note2 = False
    if len(note2) > 0:
        include_note2 = True
    if invoice.given_data['bank_ref'] is None:
        is_wire = False
    else:
        is_wire = True

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'currency': render.escape_latex(invoice.currency.symbol),
             'inv_total':
             render.escape_latex(invoice.extendedtotal.source_string),
             'exchrate': invoice.given_data['exchrate'],
             'exchnotif': invoice.given_data['exchnotif'],
             'exchnotifdt': invoice.given_data['exchnotif_date'],
             'note1': note1,
             'note2': note2,
             'include_note2': include_note2,
             'extended_total_sc':
             render.escape_latex(invoice.extendedtotal.source_string),
             'assessable_total_sc':
             render.escape_latex(invoice.assessabletotal.source_string),
             'assessable_total_nc':
             render.escape_latex(invoice.assessabletotal.native_string),
             'sno': serialno + '.3',
             'is_wire': is_wire
             }

    return render.render_pdf(stage, 'customs/valuation.tex', outpath)


def gen_rsp_declaration(invoice, target_folder, serialno):
    """
    Generates the Customs Retail Sales Price Declaration.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file path

    .. rubric:: Template Used

    ``tendril/dox/templates/customs/rsp-declaration.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/rsp-declaration.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at,
            from :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`
        * - ``sno``
          - The serial number of the document.

    """
    outpath = os.path.join(
        target_folder,
        "customs-rsp-declaration-" + str(invoice.inv_no) + ".pdf"
    )

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'sno': serialno + '.2'
             }

    return render.render_pdf(stage, 'customs/rsp-declaration.tex', outpath)


def gen_authorization(invoice, target_folder, serialno):
    """
    Generates the Customs CHA Authorization Letter.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file path

    .. rubric:: Template Used

    This function uses a different template for each CHA, in the format
    that the CHA asks for it.

    Template Filename :
    ``tendril/dox/templates/customs/authorization.<cha>.tex``

    Included Templates :

    .. list-table::

        * - FedEx India
          - ``tendril/dox/templates/customs/authorization.fedex.tex``
          - (:download:`Included version <../../tendril/dox/templates/\
customs/authorization.fedex.tex>`)
        * - DHL India
          - ``tendril/dox/templates/customs/authorization.dhl.tex``
          - (:download:`Included version <../../tendril/dox/templates/\
customs/authorization.dhl.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at,
            from :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`
        * - ``sno``
          - The serial number of the document.

    """
    outpath = os.path.join(
        target_folder,
        "customs-authorization-" + str(invoice.inv_no) + ".pdf"
    )
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'sno': serialno + '.1'
             }

    if invoice.given_data['cha'] == 'DHL':
        template = 'customs/authorization.dhl.tex'
    elif invoice.given_data['cha'] == 'FedEx':
        template = 'customs/authorization.fedex.tex'
    else:
        raise ValueError('CHA unsupported')
    return render.render_pdf(stage, template, outpath)


def gen_tech_writeup(invoice, target_folder, serialno):
    """
    Generates the Customs Technical Writeup.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file path

    .. rubric:: Template Used

    Template Filename :
    ``tendril/dox/templates/customs/technical-writeup.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/technical-writeup.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at,
            from :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`
        * - ``sno``
          - The serial number of the document.
        * - ``linecount``
          - The number of lines in the invoice.
        * - ``tqty``
          - The total quantity.
        * - ``tvalue``
          - The total value.
        * - ``unclassified``
          - Lines in the invoice which could not be classified
        * - ``sectable``
          - The secion table, containing a list of ``section lines``,
            described below. The 'sections' here are Customs HS Codes.

    .. list-table:: Section line keys

        * - ``code``
          - The HS section code.
        * - ``name``
          - The HS section name.
        * - ``idxs``
          - Line numbers classified into this line.
        * - ``qty``
          - Total quantity of all lines classified into this line.
        * - ``value``
          - Total value of all lines classified into this line.

    """
    outpath = os.path.join(
        target_folder,
        "customs-tech-writeup-" + str(invoice.inv_no) + ".pdf"
    )
    sectable = []
    tqty = 0
    tvalue = 0
    for section in invoice.hssections:
        lval = invoice.getsection_assessabletotal(section).source_string
        secline = {'code': section.code,
                   'name': section.name,
                   'idxs': invoice.getsection_idxs(section),
                   'qty': invoice.getsection_qty(section),
                   'value': render.escape_latex(lval)
                   }
        sectable.append(secline)
        tqty += invoice.getsection_qty(section)
        tvalue += invoice.getsection_assessabletotal(section)

    unclassified = {'idxs': [x.idx for x in invoice.unclassified],
                    'qty': sum([x.qty for x in invoice.unclassified]),
                    }
    if unclassified['qty'] > 0:
        unclassified['value'] = \
            render.escape_latex(
                sum([x.assessableprice
                     for x in invoice.unclassified]).source_string)
        tvalue += sum([x.assessableprice for x in invoice.unclassified])
        tqty += unclassified['qty']
    else:
        unclassified['value'] = None

    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'linecount': invoice.linecount,
             'sectable': sectable,
             'tqty': tqty,
             'tvalue': render.escape_latex(tvalue.source_string),
             'unclassified': unclassified,
             'sno': serialno + '.4'
             }
    return render.render_pdf(stage, 'customs/technical-writeup.tex', outpath)


def gen_submitdocs(invoice, target_folder, serialno):
    """
    Generates collated PDF files containing the submittable
    documents. Two PDF files are generated - one for printing on
    the company letterhead and one on regular paper.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: List of output file tuples (path, type)


    .. rubric:: Included Documents - For Letterhead Printing

    * CHA Authorization, generated by :func:`gen_authorization`
    * RSP Declaration, generated by :func:`gen_rsp_declaration`
    * Note on Valuation, generated by :func:`gen_valuation`
    * Technical Writeup, generated by :func:`gen_tech_writeup`

    .. rubric:: Included Documents - For Plain Paper Printing

    * Declaration (ORIGINAL), generated by :func:`gen_declaration`
    * Declaration (DUPLICATE), generated by :func:`gen_declaration`
    * Two copies of the Gatt Declaration, from :mod:`tendril.dox.wallet`,
      key ``CUSTOMS-DECL``.
    * Scanned copy of the IEC, from :mod:`tendril.dox.wallet`,
      key ``IEC``.

    """
    lh_files = [gen_authorization(invoice, target_folder, serialno),
                gen_rsp_declaration(invoice, target_folder, serialno),
                gen_valuation(invoice, target_folder, serialno),
                gen_tech_writeup(invoice, target_folder, serialno)
                ]
    lh_fpath = os.path.join(
        target_folder, "customs-printable-lh-" + str(invoice.inv_no) + ".pdf"
    )
    lh_fpath = pdf.merge_pdf(lh_files, lh_fpath, remove_sources=True)

    pp_files = [gen_declaration(invoice, target_folder,
                                'ORIGINAL', serialno),
                gen_declaration(invoice, target_folder,
                                'DUPLICATE', serialno),
                wallet.get_document_path('CUSTOMS-DECL'),
                wallet.get_document_path('CUSTOMS-DECL'),
                wallet.get_document_path('IEC'),
                ]
    pp_fpath = os.path.join(
        target_folder, "customs-printable-pp-" + str(invoice.inv_no) + ".pdf"
    )
    pp_fpath = pdf.merge_pdf(pp_files, pp_fpath, remove_sources=True)

    files = [(lh_fpath, 'CUST-PRINTABLE-LH'), (pp_fpath, 'CUST-PRINTABLE-PP')]
    return files


def gen_verification_sections(invoice, target_folder, serialno):
    """
    Generates the Customs Sections Verification document.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file tuple (path, type)

    .. rubric:: Template Used

    ``tendril/dox/templates/customs/verification-sections.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/verification-sections.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at,
            from :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`.
        * - ``lines``
          - A list of :class:`tendril.sourcing.customs.CustomsInvoiceLine`
            instances.
        * - ``sno``
          - The serial number of the document.

    """
    outpath = os.path.join(
        target_folder,
        "customs-verification-sections-" + str(invoice.inv_no) + ".pdf"
    )
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'lines': invoice.lines,
             'sno': serialno + '.6',
             }

    outpath = render.render_pdf(stage,
                                'customs/verification-sections.tex',
                                outpath)
    return outpath, 'CUST-VERIF-SEC'


def gen_verification_checklist(invoice, target_folder, serialno):
    """
    Generates the Customs Duties / Checklist Verification document.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: The output file tuple (path, type)

    .. rubric:: Template Used

    ``tendril/dox/templates/customs/verification-duties.tex``
    (:download:`Included version
    <../../tendril/dox/templates/customs/verification-duties.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``date``
          - The date the documents were generated at,
            from :func:`datetime.date.today`.
        * - ``signatory``
          - The name of the person who 'signs' the document, from
            :data:`tendril.utils.config.COMPANY_GOVT_POINT`.
        * - ``inv_no``
          - The vendor's invoice number.
        * - ``inv_date``
          - The date of the vendor's invoice.
        * - ``given_data``
          - A dict containing various facts about the invoice. See
            :attr:`tendril.sourcing.customs.CustomsInvoice.given_data`.
        * - ``lines``
          - A list of :class:`tendril.sourcing.customs.CustomsInvoiceLine`
            instances.
        * - ``invoice``
          - The :class:`tendril.sourcing.customs.CustomsInvoice` instance.
        * - ``sno``
          - The serial number of the document.
        * - ``summary``
          - A list of dicts containing the summary of the customs duties
            applicable against a particular section, as described below

    .. list-table:: Summary keys

        * - ``section``
          - The HS section, a
            :class:`tendril.sourcing.customs.CustomsSection`` instance.
        * - ``code``
          - The HS section code.
        * - ``name``
          - The HS section name.
        * - ``idxs``
          - Line numbers classified into this line.
        * - ``qty``
          - Total quantity of all lines classified into this line.
        * - ``assessablevalue``
          - Total assessable value of all lines classified into this line.
        * - ``bcd``
          - Total Basic Customs Duty applicable against this section.
        * - ``cvd``
          - Total Countervailing Duty applicable against this section.
        * - ``acvd``
          - Total Additional Countervailing Duty applicable against
            this section.
        * - ``cec``
          - Total Education Cess on Customs Duty applicable against
            this section.
        * - ``cshec``
          - Total Secondary and Higher Education Cess on Customs Duty
            applicable against this section.
        * - ``cvdec``
          - Total Education Cess on Countervailing Duty applicable
            against this section.
        * - ``cvdshec``
          - Total Secondary and Higher Education Cess on Countervailing Duty
            applicable against this section.

    """
    outpath = os.path.join(
        target_folder,
        "customs-verification-duties-" + str(invoice.inv_no) + ".pdf"
    )
    summary = []
    for section in invoice.hssections:
        secsum = {'section': section,
                  'code': section.code,
                  'name': section.name,
                  'idxs': invoice.getsection_idxs(hssection=section),
                  'assessablevalue':
                  invoice.getsection_assessabletotal(hssection=section),
                  'qty': invoice.getsection_qty(hssection=section),
                  'bcd':
                  sum([x.bcd.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'cvd':
                  sum([x.cvd.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'acvd':
                  sum([x.acvd.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'cec':
                  sum([x.cec.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'cshec':
                  sum([x.cshec.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'cvdec':
                  sum([x.cvdec.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  'cvdshec':
                  sum([x.cvdshec.value for x in
                       invoice.getsection_lines(hssection=section)]),
                  }
        summary.append(secsum)
    stage = {'date': datetime.date.today().isoformat(),
             'signatory': COMPANY_GOVT_POINT,
             'inv_no': invoice.inv_no,
             'inv_date': invoice.inv_date,
             'given_data': invoice.given_data,
             'lines': invoice.lines,
             'summary': summary,
             'invoice': invoice,
             'sno': serialno + '.7'}
    outpath = render.render_pdf(stage,
                                'customs/verification-duties.tex',
                                outpath)
    return outpath, 'CUST-VERIF-BOE'


def gen_verificationdocs(invoice, target_folder, serialno):
    """
    Generates customs verification documents.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to
    :param serialno: The serial number of the Customs documentation set
    :type serialno: str
    :return: List of output file tuples (path, type)

    .. rubric:: Included Documents

    * Sections Verification, generated by :func:`gen_verification_sections`
    * Duties / Checklist Verification, generated by
      :func:`gen_verification_checklist`

    """
    files = [gen_verification_sections(invoice, target_folder, serialno),
             gen_verification_checklist(invoice, target_folder, serialno)
             ]
    return files


def generate_docs(invoice, target_folder=None,
                  serialno=None, register=False, efield=None):
    """
    Generates all the Customs related documentation given a CustomsInvoice
    (or subclass) instance.

    :param invoice: The invoice object with customs information
    :type invoice: :class:`tendril.sourcing.customs.CustomsInvoice`
    :param target_folder: The folder in which the generated files
                          should be written to. Auto sets to Instance scratch
                          folder if None
    :type target_folder: str
    :param serialno: The serial number of the Customs documentation set.
                     Autogenerates if None.
    :type serialno: str
    :param register: Whether or not to register in the docstore.
                     Default False.
    :type register: bool
    :param efield: Additional short note to identify the document in the
                   store. Autogenerates from invoice if None.
    :type efield: str
    :return: The serial number of the generated document set.

    .. rubric:: Included Document Sets

    * Sumbmittable Documents, generated by :func:`gen_submitdocs`
    * Verification Documents, generated by :func:`gen_verificationdocs`

    """
    if efield is None:
        efield = ' '.join([invoice.vendor_name, str(invoice.inv_no)])
    if serialno is None:
        if os.path.exists(os.path.join(invoice.source_folder, 'wsno')):
            with open(os.path.join(invoice.source_folder, 'wsno'), 'r') as f:
                serialno = f.readline()
        else:
            serialno = serialnos.get_serialno(series='PINV',
                                              efield=efield,
                                              register=register)
    if target_folder is None:
        target_folder = invoice.source_folder
    files = gen_submitdocs(invoice, target_folder, serialno=serialno)
    files.extend(
        gen_verificationdocs(invoice, target_folder, serialno=serialno)
    )
    files.extend(
        invoice.source_files
    )
    if register is True:
        for document in files:
            docstore.register_document(serialno=serialno, docpath=document[0],
                                       doctype=document[1],
                                       efield=efield, series='PINV')
    return serialno


@with_db
def get_all_customs_invoice_serialnos(limit=None, session=None):
    snos = docstore.controller.get_snos_by_document_doctype(
        doctype='CUST-PRINTABLE-PP', series='PINV',
        limit=limit, session=session
    )
    return snos


def get_customs_invoice(serialno):
    documents = docstore.controller.get_sno_documents(serialno=serialno)
    inv_yaml = None
    for document in documents:
        if document.doctype == 'INVOICE-DATA-YAML':
            inv_yaml = document.docpath
    if not inv_yaml:
        raise ValueError('Invoice data not found for : ' + serialno)
    with docstore.docstore_fs.open(inv_yaml, 'r') as f:
        inv_data = yaml.load(f)

    inv_format = inv_data['invoice_format']

    if inv_format == 'analogdevices':
        from tendril.sourcing import pricelist
        invoice_class = pricelist.AnalogDevicesInvoice
    elif inv_format == 'digikey':
        from tendril.sourcing import digikey
        invoice_class = digikey.DigiKeyInvoice
    else:
        raise ValueError('Unrecognized Customs Invoice Format : ' +
                         inv_format)

    from tendril.sourcing import electronics
    vobj = electronics.get_vendor_by_name(inv_format)

    workspace_name = get_tempname()
    docstore.copy_docs_to_workspace(serialno=serialno,
                                    workspace=workspace_name,
                                    clearws=True,
                                    fs=temp_fs)

    invoice = invoice_class(
        vobj,
        temp_fs.getsyspath(
            fs.path.join(workspace_name, 'inv_data.yaml')
        )
    )

    temp_fs.removedir(workspace_name, recursive=True, force=True)
    return invoice
