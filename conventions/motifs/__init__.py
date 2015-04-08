"""
This file is part of koala
See the COPYING, README, and INSTALL files for more information
"""


def create_motif_object(motifst):
    modname = motifst.split('.')[0]
    modstr = 'conventions.motifs.' + modname
    clsname = 'Motif' + modname
    mod = __import__(modstr, fromlist=[clsname])
    cls = getattr(mod, clsname)
    instance = cls(motifst)
    return instance
