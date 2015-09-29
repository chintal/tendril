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
The Progressbar Util Module (:mod:`tendril.utils.progressbar`)
==============================================================

This package produces animated progress bars on the terminal. It is
essentially a copy of pip`s progressbar implementation in pip.utils.ui.

This module maintains the :class:`TendrilProgressBar`, which can be
used from other modules to provide a consistent feel to progress bars
across tendril. It adds a ``note`` keyword argument to the ``next()``
function, and renders the note after the suffix of the progress bar.

.. rubric :: Usage

    >>> from tendril.utils.progressbar import TendrilProgressBar
    >>> pb = TendrilProgressBar(max=100)
    >>> for i in range(100):
    ...     pb.next(note=i)

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os

import six
from time import time
from progress.bar import Bar
from progress.bar import IncrementalBar

try:
    import colorama
# Lots of different errors can come from this, including SystemError and
# ImportError.
except Exception:
    colorama = None

WINDOWS = (sys.platform.startswith("win") or
           (sys.platform == 'cli' and os.name == 'nt'))


def _select_progress_class(preferred, fallback):
    encoding = getattr(preferred.file, "encoding", None)

    # If we don't know what encoding this file is in, then we'll just assume
    # that it doesn't support unicode and use the ASCII bar.
    if not encoding:
        return fallback

    # Collect all of the possible characters we want to use with the preferred
    # bar.
    characters = [
        getattr(preferred, "empty_fill", six.text_type()),
        getattr(preferred, "fill", six.text_type()),
    ]
    characters += list(getattr(preferred, "phases", []))

    # Try to decode the characters we're using for the bar using the encoding
    # of the given file, if this works then we'll assume that we can use the
    # fancier bar and if not we'll fall back to the plaintext bar.
    try:
        six.text_type().join(characters).encode(encoding)
    except UnicodeEncodeError:
        return fallback
    else:
        return preferred

_BaseBar = _select_progress_class(IncrementalBar, Bar)


class WindowsMixin(object):

    def __init__(self, *args, **kwargs):
        # The Windows terminal does not support the hide/show cursor ANSI codes
        # even with colorama. So we'll ensure that hide_cursor is False on
        # Windows.
        # This call neds to go before the super() call, so that hide_cursor
        # is set in time. The base progress bar class writes the "hide cursor"
        # code to the terminal in its init, so if we don't set this soon
        # enough, we get a "hide" with no corresponding "show"...
        if WINDOWS and self.hide_cursor:
            self.hide_cursor = False

        super(WindowsMixin, self).__init__(*args, **kwargs)

        # Check if we are running on Windows and we have the colorama module,
        # if we do then wrap our file with it.
        if WINDOWS and colorama:
            self.file = colorama.AnsiToWin32(self.file)
            # The progress code expects to be able to call self.file.isatty()
            # but the colorama.AnsiToWin32() object doesn't have that, so we'll
            # add it.
            self.file.isatty = lambda: self.file.wrapped.isatty()
            # The progress code expects to be able to call self.file.flush()
            # but the colorama.AnsiToWin32() object doesn't have that, so we'll
            # add it.
            self.file.flush = lambda: self.file.wrapped.flush()


class TendrilProgressBar(WindowsMixin, _BaseBar):
    file = sys.stdout
    message = "%(percent)3d%%"
    suffix = "ETA %(eta_td)s"

    def __init__(self, *args, **kwargs):
        super(TendrilProgressBar, self).__init__(*args, **kwargs)
        self._note = None

    def next(self, n=1, note=None):
        if n > 0:
            now = time()
            dt = (now - self._ts) / n
            self._dt.append(dt)
            self._ts = now

        self.index += n
        self._note = repr(note)
        self.update()

    def writeln(self, line):
        if self.file.isatty():
            self.clearln()
            if self._note is not None:
                line = ' '.join([line, self._note])
                if len(line) > 80:
                    line = line[:80]
            print(line, end='', file=self.file)
            self.file.flush()
