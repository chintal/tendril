"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


class EntityBase(object):
    """ Placeholder class for potentially track-able objects.

        Depending on the implementation used, this class should inherit from
        an external class built for this purpose instead of from ``object``.

    """
    def __init__(self):
        pass

    @property
    def ident(self):
        raise NotImplementedError


class EntityGroupBase(EntityBase):
    def __init__(self):
        super(EntityGroupBase, self).__init__()

    @property
    def ident(self):
        raise NotImplementedError


class EntityBomBase(EntityBase):
    def __init__(self):
        super(EntityBomBase, self).__init__()

    @property
    def ident(self):
        raise NotImplementedError
