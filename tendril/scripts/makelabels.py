"""
This file is part of tendril
See the COPYING, README, and INSTALL files for more information
"""
from tendril.libraries import products as product_library
from tendril.entities.products import prototype
from tendril.entityhub.db import controller
from tendril.entityhub import serialnos
from tendril.config.legacy import INSTANCE_ROOT
from tendril.dox.labelmaker import manager


if __name__ == '__main__':
    snos = [x.sno for x in
            controller.get_serialnos_by_efield(efield="QSENS-ACCEL1-1.7G")
            ]
    #snos += [x.sno for x in
    #        controller.get_serialnos_by_efield(efield="QASC-T1-RTD-R3")
    #        ]
    #snos += [x.sno for x in
    #        controller.get_serialnos_by_efield(efield="QASC-LVDT-AD598-R2")
    #        ]
    #snos += [x.sno for x in
    #        controller.get_serialnos_by_efield(efield="CBL-STRAIN-HBC-A-120E")
    #        ]
    #snos += [x.sno for x in
    #         controller.get_serialnos_by_efield(efield="CBL-STRAIN-QBC-120E")
    #         ]
    #snos += [x.sno for x in
    #         controller.get_serialnos_by_efield(efield="CBL-PIEZO")
    #         ]
    for sno in snos:
        product = product_library.get_product_by_core(serialnos.get_serialno_efield(sno=sno))  # noqa
        if product is not None:
            prototype.generate_labels(product, sno)
    manager.generate_pdfs(INSTANCE_ROOT, force=True)
