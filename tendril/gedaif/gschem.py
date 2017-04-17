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
gEDA gschem module documentation (:mod:`gedaif.gschem`)
=======================================================
"""

import re
import os
import subprocess

from tendril.conventions.electronics import parse_ident

from tendril.utils import vcs
from tendril.utils.files import pdf
from tendril.utils.files import gschem as gschf
from tendril.utils.config import GEDA_SCHEME_DIR
from tendril.utils.config import USE_SYSTEM_GAF_BIN
from tendril.utils.config import GAF_BIN_ROOT
from tendril.utils.config import PROJECTS_ROOT
from tendril.utils.config import COMPANY_SQUARE_LOGO_PATH
from tendril.utils.config import INSTANCE_ROOT

try:
    import sym2eps
except ImportError:
    sym2eps = None

import tendril.utils.log
logger = tendril.utils.log.get_logger(__name__, tendril.utils.log.INFO)

rex_titleblocks = re.compile(r"^S-TITLE-A\d.sym$")


def rewrite_schematic(inpath, obom, gpf, outpath):
    fbase = os.path.split(inpath)[1]
    f = gschf.GschFile(inpath)
    # Replace value strings with whatever the bom says
    for c in f.components:
        # TODO Review possibility of reconstructing from the BOM instead
        # of the relatively more expensive OBOM parsing.
        item = obom.get_item_for_refdes(c.refdes)
        if not item:
            result = c.set_attribute('fillstatus', 'DNP')
            if not result:
                c.set_attribute('value', 'DNP')
            continue
        fstatus = c.get_attribute('fillstatus')
        if fstatus == 'CONF':
            c.remove_attribute('fillstatus')
        d, v, fp = parse_ident(item.ident)
        c.value = v
    # Handle Titleblocks
    tbs = f.get_meta_components(rex_titleblocks)
    if len(tbs):
        tb = tbs[0]
        tb._selectable = 1
        tb.set_attribute('PN', obom.descriptor.pcbname)
        tb.set_attribute('CN', obom.descriptor.configname)
        tb.set_attribute('MAINTAINER',
                         obom.descriptor.configurations.maintainer)
        tb.set_attribute('DGR',
                         obom.descriptor.configurations.file_groups.get(
                             fbase, 'default')
                         )
        tb.set_attribute('NP', len(gpf.schfiles))
        tb.set_attribute('P', gpf.schfiles.index(fbase) + 1)

        wcroot = vcs.get_path_wcroot(inpath)
        rev = vcs.get_file_revision(inpath)
        fpath = os.path.relpath(inpath, wcroot)
        frev = vcs.get_path_revision(inpath)
        tb.set_attribute('RR', '{0}:r{1}'.format(
            os.path.relpath(wcroot, PROJECTS_ROOT), rev))
        tb.set_attribute('RP', '{0}:r{1}'.format(fpath, frev))

        lx, ly, lw, lh = map(int, tb.get_attribute('logo')[1:-1].split(','))
        lx += getattr(tb, '_x')
        ly += getattr(tb, '_y')
        tb.remove_attribute('logo')
        lines = gschf.GschFakeLines([
            os.path.join(INSTANCE_ROOT, COMPANY_SQUARE_LOGO_PATH)
        ])
        logo = gschf.GschElementPicture(f, lines, lx, ly, lw, lh, 0, 0, 0)
        f.add_element(logo)
    f.write_out(outpath)


def conv_gsch2pdf(schpath, docfolder):
    schpath = os.path.normpath(schpath)
    schfname = os.path.splitext(os.path.split(schpath)[1])[0]
    pspath = os.path.join(docfolder, schfname + '.ps')
    pdfpath = os.path.join(docfolder, schfname + '.pdf')
    # TODO fix this
    if USE_SYSTEM_GAF_BIN:
        gschem_pscmd = "gschem -o" + pspath + \
                       " -s" + GEDA_SCHEME_DIR + '/print.scm ' + schpath
        subprocess.call(gschem_pscmd.split(' '))
        pdf.conv_ps2pdf(pspath, pdfpath)
        os.remove(pspath)
    else:
        gaf_pdfcmd = [os.path.join(GAF_BIN_ROOT, 'gaf'),
                      'export', '-o', pdfpath, '-c',
                      schpath]
        subprocess.call(gaf_pdfcmd)
    return pdfpath


def conv_gsch2png(schpath, outfolder, include_extension=False):
    schpath = os.path.normpath(schpath)
    if include_extension is False:
        schfname, ext = os.path.splitext(os.path.split(schpath)[1])
    else:
        schfname = os.path.split(schpath)[1]

    outpath = os.path.join(outfolder, schfname + '.png')
    epspath = os.path.join(outfolder, schfname + '.eps')

    if USE_SYSTEM_GAF_BIN and sym2eps:
        try:
            sym2eps.convert(schpath, epspath)
        except RuntimeError:
            logger.error(
                "SYM2EPS Segmentation Fault on symbol : " + schpath
            )
        gschem_pngcmd = [
            "convert", epspath, "-transparent", "white", outpath
        ]
        subprocess.call(gschem_pngcmd)
        try:
            os.remove(epspath)
        except OSError:
            logger.warning("Temporary .eps file not found to remove : " +
                           epspath)
    else:
        gaf_pngcmd = [
            os.path.join(GAF_BIN_ROOT, 'gaf'),
            'export', '-c', '-o', outpath,
            schpath
        ]
        subprocess.call(gaf_pngcmd)
    return outpath


if __name__ == "__main__":
    pass
