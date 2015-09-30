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
Docstring for test_utils_www
"""

import six
from tendril.utils import www
from hashlib import md5
import pytest
from six.moves.urllib.error import HTTPError, URLError
www.DUMP_REDIR_CACHE_ON_EXIT = False


def test_www_strencode():
    pairs = [
        (u'Test String', b'Test String'),
        (u'', b''),
        (u'\u00b5ACD', b'uACD'),
        (u'\u00b11323', b'+/-1323'),
    ]
    for inp, outp in pairs:
        assert www.strencode(inp) == outp


def test_www_opener():
    pass


def test_redirect_cache_301():
    www.ENABLE_REDIRECT_CACHING = True
    assert isinstance(www.redirect_cache, dict)
    result = www.urlopen('https://jigsaw.w3.org/HTTP/300/301.html')
    assert result.status == 301
    newtarget = www.get_actual_url('https://jigsaw.w3.org/HTTP/300/301.html')
    assert newtarget == 'https://jigsaw.w3.org/HTTP/300/Overview.html'
    result = www.urlopen('https://jigsaw.w3.org/HTTP/300/301.html')
    assert hasattr(result, 'status') == False or result.status == 200


def test_redirect_cache_302():
    www.ENABLE_REDIRECT_CACHING = True
    result = www.urlopen('https://jigsaw.w3.org/HTTP/300/302.html')
    assert result.status == 302
    newtarget = www.get_actual_url('https://jigsaw.w3.org/HTTP/300/302.html')
    assert newtarget == 'https://jigsaw.w3.org/HTTP/300/302.html'
    result = www.urlopen('https://jigsaw.w3.org/HTTP/300/302.html')
    assert result.status == 302


def test_disabled_redirect_caching():
    www.ENABLE_REDIRECT_CACHING = False
    result = www.urlopen('https://jigsaw.w3.org/HTTP/300/301.html')
    assert result.status == 301
    newtarget = www.get_actual_url('https://jigsaw.w3.org/HTTP/300/301.html')
    assert newtarget == 'https://jigsaw.w3.org/HTTP/300/301.html'


def test_cached_fetcher():
    test_url = 'http://www.google.com'
    if six.PY3:
        filepath = md5(test_url.encode('utf-8')).hexdigest()
    else:
        filepath = md5(test_url).hexdigest()
    fs = www.cached_fetcher.cache_fs
    if fs.exists(filepath):
        fs.remove(filepath)
    soup = www.get_soup('http://www.google.com')
    assert soup is not None
    assert fs.exists(filepath)


def test_www_errors():
    with pytest.raises(HTTPError):
        www.get_soup('http://httpstat.us/404')
    with pytest.raises(URLError):
        www.get_soup('httpd://httpstat.us/404')
    result = www.urlopen('http://httpstat.us/500')
    assert result is None
