"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


def generate_docs(invoice, target_folder=None):
    if target_folder is None:
        target_folder = invoice.source_folder
