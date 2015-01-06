"""
WWW Utils Module Documentation (:mod:`utils.wwwutils`)
======================================================
"""

import urllib2


def _create_opener():
    openr = urllib2.build_opener()
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr

opener = _create_opener()
