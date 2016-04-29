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
Production Dox Module (:mod:`tendril.dox.production`)
=====================================================

This module provides functions to generate production related documentation.
The functions here use the :mod:`tendril.dox.render` module to actually
produce the output files after constructing the appropriate stage.

.. seealso:: :mod:`tendril.dox`

.. rubric:: Document Generators

.. autosummary::

    gen_pcb_am
    gen_production_order

"""

import os

from fs.utils import copyfile

import docstore
import render
from tendril.boms.outputbase import DeltaOutputBom
from tendril.entityhub import projects
from tendril.entityhub import serialnos
from tendril.entityhub.modules import get_module_instance
from tendril.entityhub.modules import get_module_prototype
from tendril.gedaif.conffile import ConfigsFile
from tendril.utils import log
from tendril.utils.fsutils import get_tempname
from tendril.utils.fsutils import temp_fs
from tendril.utils.files.pdf import merge_pdf
logger = log.get_logger(__name__, log.DEBUG)


def gen_pcb_am(configname, outfolder, sno=None, productionorderno=None,
               indentsno=None, scaffold=False, verbose=True, session=None):
    """
    Generates a PCB Assembly Manifest for a 'card', a card being defined as a
    gEDA project, with a specified ``configname``.

    In the present implementation, the project could provide either a PCB or a
    Cable.

        - In case the project provides the card, the schematic for the cable
          is included along with the assembly manifest.
        - In case the project provides a PCB, the schematic is not included
          with the assembly manifest.

    This behavior is not really intuitive nor universally desirable. This
    rationale should be changed to something that makes more sense.

    .. note::
        This function does not register the document in the
        :mod:`tendril.dox.docstore`. You should use the output file path
        (returned by this function) to register the document when desired.

    .. seealso::
        - :mod:`tendril.gedaif.conffile`, for information about confignames.
        - :mod:`tendril.entityhub.projects`, for information about 'cards'

    .. todo:: Update this function to also handle registering once the main
              scripts are better integrated into the core.

    :param configname: The name of the project configuration to use.
    :type configname: str
    :param outfolder: The folder within which the output file should be
                      created.
    :type outfolder: str
    :param sno: The serial number of the card for which you want the Assembly
                Manifest.
    :type sno: str
    :param productionorderno: The serial number of the Production Order for
                              the card.
    :type productionorderno: str
    :param indentsno: The serial number of the Stock Indent which accounts for
                      the components used in this card.
    :type indentsno: str
    :return: The path of the generated file.

    .. rubric:: Template Used

    ``tendril/dox/templates/production/pcb-assem-manifest.tex``
    (:download:`Included version
    <../../tendril/dox/templates/production/pcb-assem-manifest.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``sno``
          - The serial number of the card.
        * - ``configname``
          - The configuration name of the card.
        * - ``pcbname``
          - The name of the PCB provided by the gEDA project.
        * - ``title``
          - Whether the device is a PCB or a Cable.
        * - ``desc``
          - The description of the card.
        * - ``lines``
          - List of :class:`tendril.boms.outputbase.OutputBomLine` instances.
        * - ``stockindent``
          - The serial number of the Stock Indent which accounts for
            the components used in this card.
        * - ``productionorderno``
          - The serial number of the Production Order for the card.
        * - ``repopath``
          - The root of the VCS repository which contains the gEDA project.
        * - ``evenpages``
          - Whether to render PDF with even number of pages by adding an extra
            page if needed (useful for bulk printing).

    """
    if sno is None:
        # TODO Generate real S.No. here
        sno = 1

    outpath = os.path.join(outfolder,
                           'am-' + configname + '-' + str(sno) + '.pdf')

    instance = get_module_instance(sno, configname,
                                   scaffold=scaffold, session=session)
    obom = instance.obom

    if projects.check_module_is_card(configname):
        entityname = instance.pcbname
        title = 'PCB '
        evenpages = True
        add_schematic = False
    elif projects.check_module_is_cable(configname):
        entityname = instance.cblname
        title = 'Cable '
        evenpages = False
        add_schematic = True
    else:
        raise ValueError

    stage = {'configname': obom.descriptor.configname,
             'pcbname': entityname,
             'title': title,
             'sno': sno,
             'lines': obom.lines,
             'evenpages': evenpages,
             'stockindent': indentsno,
             'repopath': projects.get_project_repo_repr(configname),
             'productionorderno': productionorderno}

    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'production/pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath, verbose=verbose)

    if add_schematic is True:
        merge_pdf([outpath,
                   os.path.join(instance.projfolder, 'doc',
                                entityname + '-schematic.pdf')],
                  outpath)
    return outpath


def gen_delta_pcb_am(orig_cardname, target_cardname, outfolder=None, sno=None,
                     productionorderno=None, indentsno=None, scaffold=False,
                     verbose=True, session=None):
    """
    Generates a Delta PCB Assembly Manifest for converting one card to
    another. This is typically only useful when the two cards are very
    closely related and use the same PCB..

    In the present implementation, the cardname could represent either a PCB
    or a Cable.

    .. note::
        This function does not register the document in the
        :mod:`tendril.dox.docstore`. You should use the output file path
        (returned by this function) to register the document when desired.

    .. seealso::
        - :mod:`tendril.entityhub.projects`, for information about 'cards'

    .. todo:: Update this function to also handle registering once the main
              scripts are better integrated into the core.

    :param orig_cardname: The name of the original card. This should be
                              present in :data:`entityhub.projects.cards`
    :type orig_cardname: str
    :param target_cardname: The name of the target card. This should be
                              present in :data:`entityhub.projects.cards`
    :type target_cardname: str
    :param outfolder: The folder within which the output file should be
                      created.
    :type outfolder: str
    :param sno: The serial number of the card for which you want the Delta
                Assembly Manifest.
    :type sno: str
    :param productionorderno: The serial number of the Production Order for
                              the modification.
    :type productionorderno: str
    :param indentsno: The serial number of the Stock Indent which accounts for
                      the components used in this card.
    :type indentsno: str
    :return: The path of the generated file.

    .. rubric:: Template Used

    ``tendril/dox/templates/production/delta-assem-manifest.tex``
    (:download:`Included version
    <../../tendril/dox/templates/production/delta-assem-manifest.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``sno``
          - The serial number of the card.
        * - ``orig_configname``
          - The configuration name of the original card.
        * - ``target_configname``
          - The configuration name of the target card.
        * - ``pcbname``
          - The name of the original PCB.
        * - ``title``
          - Whether the device is a PCB or a Cable.
        * - ``desc``
          - The description of the modification.
        * - ``addition_lines``
          - List of :class:`tendril.boms.outputbase.OutputBomLine` instances.
        * - ``subtraction_lines``
          - List of :class:`tendril.boms.outputbase.OutputBomLine` instances.
        * - ``stockindent``
          - The serial number of the Stock Indent which accounts for
            the components used in this card.
        * - ``productionorderno``
          - The serial number of the Production Order for the card.
        * - ``original_repopath``
          - The root of the VCS repository which contains the original gEDA project.
        * - ``target_repopath``
          - The root of the VCS repository which contains the target gEDA project.
        * - ``evenpages``
          - Whether to render PDF with even number of pages by adding an extra
            page if needed (useful for bulk printing).

    """

    if outfolder is None:
        from tendril.utils.config import INSTANCE_ROOT
        outfolder = os.path.join(INSTANCE_ROOT, 'scratch', 'production')

    if sno is None:
        # TODO Generate real S.No. here
        sno = 1

    outpath = os.path.join(
            outfolder,
            'dm-' + orig_cardname + '->' + target_cardname +
            '-' + str(sno) + '.pdf'
    )

    orig_instance = get_module_instance(sno, orig_cardname,
                                        session=session, scaffold=True)
    orig_obom = orig_instance.obom
    target_instance = get_module_prototype(target_cardname)
    target_obom = target_instance.obom

    delta_obom = DeltaOutputBom(orig_obom, target_obom)

    if projects.check_module_is_card(orig_cardname):
        orig_entityname = orig_instance.pcbname
        try:
            target_entityname = target_instance.pcbname
        except AttributeError:
            logger.error("Target for the delta should be a PCB!")
            raise
        title = 'PCB '
        evenpages = True
    elif projects.check_module_is_cable(orig_cardname):
        orig_entityname = orig_instance.cblname
        try:
            target_entityname = target_instance.cblname
        except AttributeError:
            logger.error("Target for the delta should be a Cable!")
            raise
        title = 'Cable '
        evenpages = False
    else:
        raise ValueError

    stage = {'orig_configname': orig_cardname,
             'target_configname': target_cardname,
             'pcbname': orig_entityname,
             'title': title,
             'sno': sno,
             'addition_lines': delta_obom.additions_bom.lines,
             'subtraction_lines': delta_obom.subtractions_bom.lines,
             'evenpages': evenpages,
             'stockindent': indentsno,
             'orig_repopath': projects.get_project_repo_repr(orig_cardname),
             'target_repopath': projects.get_project_repo_repr(target_cardname),  # noqa
             'productionorderno': productionorderno,
             'desc': delta_obom.descriptor.configname}

    template = 'production/delta-assem-manifest.tex'

    render.render_pdf(stage, template, outpath, verbose=verbose)
    return outpath


def gen_production_order(outfolder, prod_sno, sourcedata, snos,
                         sourcing_orders=None, root_orders=None,
                         verbose=True):
    """
    Generates a Production Order for a production order defined in a
    ``.yaml`` file.

    .. note::
        This function does not register the document in the
        :mod:`tendril.dox.docstore`. You should use the output file path
        (returned by this function) to register the document when desired.

    .. todo:: Update this function to also handle registering once the main
              scripts are better integrated into the core.

    .. todo:: Document the format of the .yaml file.

    :param outfolder: The folder within which the output file
                      should be created.
    :type outfolder: str
    :param prod_sno: The serial number of the Production Order to generate.
    :type prod_sno: str
    :param sourcedata: The source data loaded from a ``.yaml`` file.
    :type sourcedata: dict
    :param snos: A list of serial numbers to produce, along with whatever
                 other information should be included in the order. See
                 the template for details.
    :type snos: :class:`list` of :class:`dict`
    :param sourcing_orders: A list of sourcing orders which were made to
                            obtain raw materials for this production order.
    :type sourcing_orders: :class:`list` of :class:`str`
    :param root_orders: A list of root orders which is production order is
                        intended to fulfill.
    :type root_orders: :class:`list` of :class:`str`
    :return: The path to the output PDF file.

    .. rubric:: Template Used

    ``tendril\dox\\templates\production\production-order-template.tex``
    (:download:`Included version
    <../../tendril/dox/templates/production/production-order-template.tex>`)

    .. rubric:: Stage Keys Provided
    .. list-table::

        * - ``sno``
          - The serial number of the production order.
        * - ``title``
          - The title of the production order.
        * - ``cards``
          - A list of different card types to be produced,
            and quantities of each.
        * - ``snos``
          - A list of cards to produce, with serial numbers and other included
            information.
        * - ``sourcing_orders``
          - A list of sourcing orders which were made to obtain raw materials
            for this production order.
        * - ``root_orders``
          - A list of root orders which is production order is
            intended to fulfill.

    """

    cards = []
    if 'cards' in sourcedata.keys():
        cards = [{'qty': sourcedata['cards'][k],
                  'desc': ConfigsFile(projects.cards[k]).description(k),
                  'ident': k} for k in sorted(sourcedata['cards'].keys())]

    deltas = {}
    if 'deltas' in sourcedata.keys():
        for delta in sourcedata['deltas']:
            desc = delta['orig-cardname'] + ' -> ' + delta['target-cardname']
            if desc in deltas.keys():
                deltas[desc] += 1
            else:
                deltas[desc] = 1

    lroot_orders = []
    for root_order in root_orders:
        if root_order is not None:
            try:
                root_order_desc = serialnos.get_serialno_efield(root_order)
            except AttributeError:
                root_order_desc = None
        else:
            root_order_desc = None
        lroot_orders.append({'no': root_order, 'desc': root_order_desc})

    stage = {
        'title': sourcedata['title'],
        'cards': cards,
        'deltas': deltas,
        'sourcing_orders': sourcing_orders,
        'sno': prod_sno,
        'snos': snos,
        'root_orders': lroot_orders,
    }

    outpath = os.path.join(outfolder, str(prod_sno) + '.pdf')
    template = 'production/production-order-template.tex'
    render.render_pdf(stage, template, outpath, verbose=verbose)
    return outpath


def get_production_order_manifest_set(serialno):
    workspace = temp_fs.makeopendir(get_tempname())
    children = serialnos.get_child_serialnos(sno=serialno)
    manifests = []
    for child in children:
        files = []

        am = docstore.get_docs_list_for_sno_doctype(serialno=child,
                                                    doctype='ASSEMBLY MANIFEST')
        if len(am) == 1:
            uam = am[0]
            copyfile(uam.fs, uam.path, workspace, uam.filename, overwrite=True)
            files = [workspace.getsyspath(uam.filename)]
        elif len(am) > 1:
            raise ValueError(
                    "Found {0} manifests for {2}".format(len(am), child)
            )

        dms = docstore.get_docs_list_for_sno_doctype(
                serialno=child, doctype='DELTA ASSEMBLY MANIFEST'
        )
        if len(dms):
            for dm in dms:
                copyfile(dm.fs, dm.path, workspace, dm.filename,
                         overwrite=True)
                files.append(workspace.getsyspath(dm.filename))

        if len(files) > 1:
            wdmfile = merge_pdf(
                files,
                os.path.join(workspace.getsyspath('/'),
                             os.path.splitext(am[0].filename)[0] + '-wdm.pdf'),
                remove_sources=True
            )
            manifests.append(wdmfile)
        elif len(files) == 1:
            manifests.append(files[0])

    if len(manifests):
        output = merge_pdf(
            manifests,
            os.path.join(workspace.getsyspath('/'), serialno + '.pdf'),
            remove_sources=True
        )
        return output
    return None


def get_production_strategy(cardname):
    # Alternate is ready.
    try:
        cardfolder = projects.cards[cardname]
    except KeyError:
        logger.error("Could not find Card in entityhub.cards")
        raise KeyError
    cardconf = ConfigsFile(cardfolder)

    prodst = None
    lblst = None
    testst = None
    genmanifest = False

    if cardconf.configdata['documentation']['am'] is True:
        # Assembly manifest should be used
        prodst = "@AM"
        genmanifest = True
    elif cardconf.configdata['documentation']['am'] is False:
        # No Assembly manifest needed
        prodst = "@THIS"
    if cardconf.configdata['productionstrategy']['testing'] == 'normal':
        # Normal test procedure, Test when made
        testst = "@NOW"
    if cardconf.configdata['productionstrategy']['testing'] == 'lazy':
        # Lazy test procedure, Test when used
        testst = "@USE"
    if cardconf.configdata['productionstrategy']['labelling'] == 'normal':
        # Normal test procedure, Label when made
        lblst = "@NOW"
    if cardconf.configdata['productionstrategy']['testing'] == 'lazy':
        # Lazy test procedure, Label when used
        lblst = "@USE"
    series = cardconf.configdata['snoseries']
    genlabel = False
    labels = []
    if isinstance(cardconf.configdata['documentation']['label'], dict):
        for k in sorted(cardconf.configdata['documentation']['label'].keys()):
            labels.append(
                {'code': k,
                 'ident': cardname + '.' + cardconf.configdata['label'][k]}
            )
        genlabel = True
    elif isinstance(cardconf.configdata['documentation']['label'], str):
        labels.append(
            {'code': cardconf.configdata['documentation']['label'],
             'ident': cardname}
        )
        genlabel = True

    return prodst, lblst, testst, genmanifest, genlabel, series, labels


def get_all_prodution_order_snos(limit=None):
    snos = docstore.controller.get_snos_by_document_doctype(
        doctype='PRODUCTION ORDER', limit=limit
    )
    rval = {'snos': []}
    for sno in snos:
        rval['snos'].append({'sno': sno.sno, 'title': sno.efield})
    return rval


def get_all_prodution_order_snos_strings(limit=None):
    snos = docstore.controller.get_snos_by_document_doctype(
        doctype='PRODUCTION ORDER', limit=limit
    )
    return [x.sno for x in snos]


def get_all_production_orders_docs(limit=None):
    return docstore.get_docs_list_for_sno_doctype(
        serialno=None, doctype='PRODUCTION ORDER', limit=limit
    )
