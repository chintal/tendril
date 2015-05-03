"""
Production Dox module documentation (:mod:`dox.production`)
============================================================
"""

import render
import os


def gen_stock_idt_from_cobom(outfolder, sno, title, carddict, cobom):

    outpath = os.path.join(outfolder,  'indent-qda-' + str(sno) + '.pdf')
    cards = ""
    for card, qty in sorted(carddict.iteritems()):
        cards += card + ' x' + str(qty) + ', '

    lines = []
    for line in cobom.lines:
        lines.append({'ident': line.ident, 'qty': line.quantity})

    stage = {'title': title,
             'sno': sno,
             'lines': lines,
             'cards': cards}

    template = 'indent_stock_template.tex'
    render.render_pdf(stage, template, outpath)

    labelpath = os.path.splitext(outpath)[0] + '-labels.pdf'
    template = 'label_stock_template.tex'
    render.render_pdf(stage, template, labelpath)

    return outpath

