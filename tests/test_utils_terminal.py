#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Chintalagiri Shashank
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
Docstring for test_utils_terminal
"""

from tendril.utils import terminal
from progress.bar import IncrementalBar


def test_terminal_width():
    width = terminal.get_terminal_width()
    assert isinstance(width, int)


def test_progressbar_base():
    assert terminal._BaseBar == IncrementalBar


def test_tendril_progressbar():
    width = terminal.get_terminal_width()

    pb = terminal.TendrilProgressBar(max=10)
    assert pb.term_width == width
    for i in range(10):
        pb.next(note=str(i))
