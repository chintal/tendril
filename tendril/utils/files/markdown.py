#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2016 Chintalagiri Shashank
#
# This file is part of tendril.
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
Docstring for markdown
"""

import re

from mistune import escape
from mistune import Renderer
from mistune import Markdown


regex_email = re.compile(ur'^<([\w]+\.*[\w]*)+@(([\w]+\.[\w]*)+)>$')


class TendrilMistuneRenderer(Renderer):
    def placeholder(self):
        return MarkdownTreeContainer()

    def block_code(self, code, lang=None):
        raise NotImplementedError

    def block_quote(self, text):
        raise NotImplementedError

    def block_html(self, html):
        raise NotImplementedError

    def header(self, text, level, raw=None):
        return 'h{0}'.format(level), text

    def hrule(self):
        raise NotImplementedError

    def list(self, body, ordered=True):
        ltype = 'unordered_list'
        if ordered:
            ltype = 'ordered_list'
        return ltype, body

    def list_item(self, text):
        return 'list_item', text

    def paragraph(self, text):
        return 'paragraph', text

    def table(self, header, body):
        raise NotImplementedError

    def table_row(self, content):
        raise NotImplementedError

    def table_cell(self, content, **flags):
        raise NotImplementedError

    def double_emphasis(self, text):
        raise NotImplementedError

    def emphasis(self, text):
        raise NotImplementedError

    def codespan(self, text):
        raise NotImplementedError

    def linebreak(self):
        raise NotImplementedError

    def strikethrough(self, text):
        raise NotImplementedError

    def text(self, text):
        return 'text', escape(text)

    def autolink(self, link, is_email=False):
        text = link = escape(link)
        if is_email:
            link = 'mailto:%s' % link
            ltype = 'email'
        else:
            ltype = 'link'
        return ltype, link, text

    def link(self, link, title, text):
        raise NotImplementedError

    def image(self, src, title, text):
        raise NotImplementedError

    def inline_html(self, html):
        # TODO we're only doing the bare minimum here to handle
        # mislabelled email addresses.
        m = regex_email.match(html)
        if m:
            email = m.groups()[0] + '@' + m.groups()[1]
            return 'email', 'mailto:' + email, email

    def newline(self):
        raise NotImplementedError

    def footnote_ref(self, key, index):
        raise NotImplementedError

    def footnote_item(self, key, text):
        raise NotImplementedError

    def footnotes(self, text):
        raise NotImplementedError


class MarkdownTreeContainer(object):
    def __init__(self):
        self._pieces = []
        # print "Creating {}".format(self)

    def __iadd__(self, other):
        # print "Adding to {} : {}".format(self, other)
        self._pieces.append(other)
        return self

    def collapse_to_text(self):
        out = ''
        for piece in self._pieces:
            if isinstance(piece, MarkdownTreeContainer):
                out += piece.collapse_to_text()
            elif piece[0] == 'text':
                out += piece[1]
        return out

    def collapse_to_markup(self):
        raise NotImplementedError


def parse_markdown(fpath):
    with open(fpath, 'r') as f:
        text = f.read()
    md = Markdown(renderer=TendrilMistuneRenderer())
    return md(text)
