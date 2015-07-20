"""
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""

import render
import os

import labelmaker


def gen_stock_idt_from_cobom(outfolder, sno, title, carddict, cobom):

    outpath = os.path.join(outfolder, str(sno) + '.pdf')
    cards = ""
    for card, qty in sorted(carddict.iteritems()):
        cards += card + ' x' + str(qty) + ', '

    indentsno = sno

    lines = []
    for idx, line in enumerate(cobom.lines):
        lines.append({'ident': line.ident, 'qty': line.quantity})
        labelmaker.manager.add_label('IDT', line.ident, indentsno + '.' + str(idx), qty=line.quantity)

    stage = {'title': title,
             'sno': indentsno,
             'lines': lines,
             'cards': cards}

    template = 'indent_stock_template.tex'
    render.render_pdf(stage, template, outpath)

    return outpath, indentsno
