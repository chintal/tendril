"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""
import os
import csv
import logging

class EntityBase(object):
    id = None

    def __init__(self):
        pass


class EntityElnComp(EntityBase):
    """ Container for a single Electronic component

    Attributes:
        refdes
        device
        value
        footprint
        inventory_link
        parent_group

    """
    def __init__(self):
        super(EntityElnComp, self).__init__()

        pass


class EntityGroup(EntityBase):
    """ Container for a group of entities

    Attributes:
        groupname
        eln_comp_list
        parent_bom

    """
    def __init__(self):
        super(EntityGroup, self).__init__()
        pass


class EntityBomConf(EntityBase):
    """A single BOM configuration

    Information only class for a single configuration
    of a single PCB.

    Attributes:
        configname
        grouplist
        parent_bom

    """
    def __init__(self):
        super(EntityBomConf, self).__init__()
        pass


class EntityBom(EntityBase):
    """Single Bill of Materials Container

    An EntityBom is a collection of EntityGroups,

    Attributes:
        configurations
        grouplist

    """
    def __init__(self):
        super(EntityBom, self).__init__()
        pass


def import_pcb(pcbfolder):
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    import_pcb("/home/chintal/code/koala/scratch")
