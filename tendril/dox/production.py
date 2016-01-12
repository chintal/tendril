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
import yaml

from fs.utils import copyfile

from tendril.boms import electronics as boms_electronics
from tendril.boms.outputbase import DeltaOutputBom

from tendril.entityhub import projects
from tendril.entityhub import serialnos
from tendril.gedaif.conffile import ConfigsFile
from tendril.utils.fsutils import temp_fs
from tendril.utils.fsutils import get_tempname
from tendril.utils.pdf import merge_pdf

import render
import docstore

from tendril.utils import log
logger = log.get_logger(__name__, log.DEBUG)


def gen_pcb_am(projfolder, configname, outfolder, sno=None,
               productionorderno=None, indentsno=None):
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

    :param projfolder: The folder of the gEDA project.
    :type projfolder: str
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

    ``tendril\dox\\templates\pcb-assem-manifest.tex``
    (:download:`Included version
    <../../tendril/dox/templates/pcb-assem-manifest.tex>`)

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

    bom = boms_electronics.import_pcb(projfolder)
    obom = bom.create_output_bom(configname)

    if bom.configurations.rawconfig['pcbname'] is not None:
        entityname = bom.configurations.rawconfig['pcbname']
        title = 'PCB '
        evenpages = True
        add_schematic = False
    elif bom.configurations.rawconfig['cblname'] is not None:
        entityname = bom.configurations.rawconfig['cblname']
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
             'repopath': projects.card_reporoot[obom.descriptor.configname],
             'productionorderno': productionorderno}

    for config in obom.descriptor.configurations.configurations:
        if config['configname'] == configname:
            stage['desc'] = config['desc']

    template = 'pcb-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)

    if add_schematic is True:
        merge_pdf([outpath,
                   os.path.join(projfolder, 'doc',
                                entityname + '-schematic.pdf')],
                  outpath)
    return outpath


def gen_delta_obom(orig_cardname, target_cardname):

    orig_bom = boms_electronics.import_pcb(projects.cards[orig_cardname])
    orig_obom = orig_bom.create_output_bom(orig_cardname)

    target_bom = boms_electronics.import_pcb(projects.cards[target_cardname])
    target_obom = target_bom.create_output_bom(target_cardname)

    return DeltaOutputBom(orig_obom, target_obom)


def gen_delta_pcb_am(orig_cardname, target_cardname,
                     outfolder=None, sno=None,
                     productionorderno=None, indentsno=None):
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
    :param orig_cardname: The name of the target card. This should be
                              present in :data:`entityhub.projects.cards`
    :type orig_cardname: str
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

    ``tendril\dox\\templates\production\delta-assem-manifest.tex``
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

    orig_bom = boms_electronics.import_pcb(projects.cards[orig_cardname])
    orig_obom = orig_bom.create_output_bom(orig_cardname)

    target_bom = boms_electronics.import_pcb(projects.cards[target_cardname])
    target_obom = target_bom.create_output_bom(target_cardname)

    delta_obom = DeltaOutputBom(orig_obom, target_obom)

    if orig_bom.configurations.rawconfig['pcbname'] is not None:
        orig_entityname = orig_bom.configurations.rawconfig['pcbname']
        try:
            target_entityname = target_bom.configurations.rawconfig['pcbname']
        except KeyError:
            logger.error("Target for the delta should be a PCB!")
            raise
        title = 'PCB '
        evenpages = True
    elif orig_bom.configurations.rawconfig['cblname'] is not None:
        orig_entityname = orig_bom.configurations.rawconfig['cblname']
        try:
            target_entityname = target_bom.configurations.rawconfig['cblname']
        except KeyError:
            logger.error("Target for the delta should be a Cable!")
            raise
        title = 'Cable '
        evenpages = False
    else:
        raise ValueError

    stage = {'orig_configname': orig_obom.descriptor.configname,
             'target_configname': target_obom.descriptor.configname,
             'pcbname': orig_entityname,
             'title': title,
             'sno': sno,
             'addition_lines': delta_obom.additions_bom.lines,
             'subtraction_lines': delta_obom.subtractions_bom.lines,
             'evenpages': evenpages,
             'stockindent': indentsno,
             'orig_repopath': projects.card_reporoot[orig_cardname],
             'target_repopath': projects.card_reporoot[target_cardname],
             'productionorderno': productionorderno,
             'desc': delta_obom.descriptor.configname}

    template = 'production/delta-assem-manifest.tex'

    render.render_pdf(stage, template, outpath)
    return outpath


def gen_production_order(outfolder, prod_sno, sourcedata, snos,
                         sourcing_orders=None, root_orders=None):
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
    render.render_pdf(stage, template, outpath)
    return outpath


def get_production_strategy(cardname):
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


def get_all_production_orders(limit=None):
    return docstore.get_docs_list_for_sno_doctype(
        serialno=None, doctype='PRODUCTION ORDER', limit=limit
    )


def get_production_order_docs(serialno=None):
    rval = []
    rval.extend(docstore.get_docs_list_for_serialno(serialno=serialno))
    return rval


def get_production_order_data(serialno=None):

    order_path = docstore.get_docs_list_for_sno_doctype(
        serialno=serialno, doctype='PRODUCTION ORDER YAML'
    )[0].path
    with docstore.docstore_fs.open(order_path, 'r') as f:
        order_yaml_data = yaml.load(f)

    snomap_path = docstore.get_docs_list_for_sno_doctype(
        serialno=serialno, doctype='SNO MAP'
    )[0].path
    with docstore.docstore_fs.open(snomap_path, 'r') as f:
        snomap_data = yaml.load(f)

    return order_yaml_data, snomap_data


def get_production_order_manifest_set(serialno):
    workspace = temp_fs.makeopendir(get_tempname())
    children = serialnos.get_child_serialnos(sno=serialno)
    manifests = []
    for child in children:
        am = docstore.get_docs_list_for_sno_doctype(child, 'ASSEMBLY MANIFEST')
        if len(am) == 1:
            am = am[0]
            copyfile(am.fs, am.path, workspace, am.filename, overwrite=True)
            manifests.append(workspace.getsyspath(am.filename))
    if len(manifests):
        output = merge_pdf(manifests,
                           os.path.join(
                               workspace.getsyspath('/'),
                               serialno + '.pdf'
                           ),
                           remove_sources=True)
        return output
    return None
