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
Docstring for changelog.py
"""

import arrow
from tendril.utils.files.markdown import parse_markdown
from tendril.utils.files.markdown import MarkdownTreeContainer


class ChangeLogParseError(Exception):
    pass


class ChangeLogNotFoundError(Exception):
    pass


class ChangeLogBase(object):
    child_marker = None
    child_marker_regex = None
    child_type = None
    has_title = False

    def __init__(self):
        self._title = None
        self._body = None
        self._children = []

    def _set_title(self, title):
        if isinstance(title, tuple):
            title = title[1]
        if isinstance(title, MarkdownTreeContainer):
            self._title = title.collapse_to_text()
        else:
            self._title = title

    def _check_for_marker(self, piece):
        if self.child_marker is not None:
            if piece[0] != self.child_marker:
                return False
        if self.child_marker_regex is not None:
            pass
        return True

    def _populate(self, mdtree):
        if self.has_title is True:
            self._set_title(mdtree._pieces.pop(0))

        if self.child_type is not None:
            subtree = None
            for piece in mdtree._pieces:
                if self._check_for_marker(piece):
                    if subtree is not None:
                        self._add_child(self.child_type(subtree))
                    subtree = MarkdownTreeContainer()
                    subtree += piece
                elif subtree is not None:
                    subtree += piece

            if subtree is not None:
                self._add_child(self.child_type(subtree))
        else:
            self._body = mdtree.collapse_to_text()

    def _add_child(self, child):
        self._children.append(child)

    @property
    def title(self):
        return self._title


# A specific change
class ChangeLogChange(ChangeLogBase):
    has_title = False

    def __init__(self, mdtree):
        super(ChangeLogChange, self).__init__()
        # TODO Deal with structure in body
        self._populate(mdtree)

    def __repr__(self):
        return '<ChangeLogChange {}>'.format(self._body)

    @property
    def body(self):
        return self._body


# A specific changelog entry
class ChangeLogEntry(ChangeLogBase):
    def __init__(self, mdtree):
        super(ChangeLogEntry, self).__init__()
        self._date = None
        self._author = None
        self._email = None
        self._populate(mdtree)

    @property
    def changes(self):
        return self._children

    @property
    def initials(self):
        return ''.join([x[0] for x in self._author.split()])

    @property
    def date(self):
        return self._date

    def _set_title(self, title):
        pieces = title[1]._pieces
        piece = pieces.pop(0)
        sdate, sname = piece[1].strip().split(' ', 1)
        self._date = arrow.get(sdate.strip())
        self._author = sname.strip()
        piece = pieces.pop(0)
        self._email = piece[2]

    def _populate(self, mdtree):
        self._set_title(mdtree._pieces.pop(0))
        piece = mdtree._pieces.pop(0)

        clist = piece[1]
        for item in clist._pieces:
            if item[0] == 'list_item':
                self._children.append(ChangeLogChange(item[1]))

    def __repr__(self):
        return '<ChangeLogEntry {}>'.format(self._date)


# A specific release
class ChangeLogSection(ChangeLogBase):
    child_marker = 'paragraph'
    child_marker_regex = ''
    child_type = ChangeLogEntry
    has_title = True

    def __init__(self, mdtree):
        super(ChangeLogSection, self).__init__()
        self._populate(mdtree)

    @property
    def entries(self):
        return self._children

    def __repr__(self):
        return '<ChangeLogSection {}>'.format(self._title)


# ChangeLog of a specific Part, relevent when a project is forked to create a
# new project.
class ChangeLogPart(ChangeLogBase):
    child_marker = 'h3'
    child_type = ChangeLogSection
    has_title = True

    def __init__(self, mdtree):
        super(ChangeLogPart, self).__init__()
        self._populate(mdtree)

    @property
    def sections(self):
        return self._children

    def __repr__(self):
        return '<ChangeLogPart {}>'.format(self._title)


# Specific ChangeLog File
class ChangeLog(ChangeLogBase):
    child_marker = 'h2'
    child_type = ChangeLogPart
    has_title = False

    def __init__(self, fpath):
        super(ChangeLog, self).__init__()
        self._fpath = fpath
        try:
            mdtree = parse_markdown(self._fpath)
        except IOError:
            raise ChangeLogNotFoundError(fpath)
        except NotImplementedError:
            raise ChangeLogParseError("Unsupported formatting found in {}".format(fpath))
        self._populate(mdtree)

    @property
    def parts(self):
        return self._children

    def __repr__(self):
        return '<ChangeLog from {}>'.format(self._fpath)


def get_changelog(fpath):
    cl = ChangeLog(fpath)
    return cl


