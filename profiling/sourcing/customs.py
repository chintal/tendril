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
Docstring for customs.py
"""


import os
import inspect

from ..profiler import do_profile

from tendril.dox import customs
from tendril.sourcing.digikey import DigiKeyInvoice


SCRIPT_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))
SCRIPT_FOLDER = os.path.normpath(os.path.join(SCRIPT_PATH, os.pardir))


@do_profile(os.path.join(SCRIPT_FOLDER, 'customs'))
def profile_customs_checklist(invoice, name):
    """
    This function profiles customs duty verification checklist generation for
    the given invoice.
    """
    customs.generate_docs(invoice, register=False)


def main():
    """
    """
    invoices = [(DigiKeyInvoice(), 'digikey')]
    profilers = [profile_customs_checklist]
    for profiler in profilers:
        for invoice, name in invoices:
            profiler(invoice, name)


if __name__ == '__main__':
    main()
