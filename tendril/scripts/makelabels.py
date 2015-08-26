"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""

from tendril.entityhub import products
from tendril.entityhub.db import controller
from tendril.entityhub import serialnos
from tendril.utils.config import INSTANCE_ROOT
from tendril.dox.labelmaker import manager


if __name__ == '__main__':
    # snos = controller.get_child_snos(serialno="PROD-100C7", child_series='QDA')
    # snos += controller.get_child_snos(serialno="PROD-100B9", child_series='QDA')
    snos = ['QDA-1061P', 'QDA-104PC', 'QDA-104C3']
    for sno in snos:
        product = products.get_product_by_core(serialnos.get_serialno_efield(sno=sno))
        if product is not None:
            products.generate_labels(product, sno)
    manager.generate_pdfs(INSTANCE_ROOT, force=True)
