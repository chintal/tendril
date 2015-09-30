# Copyright (C) 2015 Chintalagiri Shashank
#
# This file is part of Tendril.
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
The WWW Utils Module (:mod:`tendril.utils.www`)
===============================================

This module provides utilities to deal with the internet. All application code
should access the internet through this module, since this where support for
proxies and caching is implemented.

.. rubric:: Main Provided Methods

.. autosummary::

    strencode
    urlopen
    get_soup


This module uses the following configuration values from
:mod:`tendril.utils.config`:

.. rubric:: Basic Settings

- :data:`tendril.utils.config.ENABLE_REDIRECT_CACHING`
  Whether or not redirect caching should be used.
- :data:`tendril.utils.config.TRY_REPLICATOR_CACHE_FIRST`
  Whether or not a replicator cache should be used.

Redirect caching speeds up network accesses by saving ``301`` and ``302``
redirects, and not needing to get the correct URL on a second access. This
redirect cache is stored as a pickled object in the ``INSTANCE_CACHE``
folder. The effect of this caching is far more apparent when a replicator
cache is also used.

.. rubric:: Network Proxy Settings

- :data:`tendril.utils.config.NETWORK_PROXY_TYPE`
- :data:`tendril.utils.config.NETWORK_PROXY_IP`
- :data:`tendril.utils.config.NETWORK_PROXY_PORT`
- :data:`tendril.utils.config.NETWORK_PROXY_USER`
- :data:`tendril.utils.config.NETWORK_PROXY_PASS`

.. rubric:: Replicator Cache Settings

The replicator cache is intended to be a ``http-replicator`` instance, to be
used to cache the web pages that are accessed locally. If
``TRY_REPLICATOR_CACHE_FIRST`` is False, the replicator isn't actually going
to be hit.

- :data:`tendril.utils.config.REPLICATOR_PROXY_TYPE`
- :data:`tendril.utils.config.REPLICATOR_PROXY_IP`
- :data:`tendril.utils.config.REPLICATOR_PROXY_PORT`
- :data:`tendril.utils.config.REPLICATOR_PROXY_USER`
- :data:`tendril.utils.config.REPLICATOR_PROXY_PASS`

This module also provides the :class:`WWWCachedFetcher` class,
an instance of which is available in :data:`cached_fetcher`, which
is subsequently used by :func:`get_soup` and any application code
that want's cached results.

Overall, caching should look something like this :

- WWWCacheFetcher provides short term (~5 days)
  caching, aggressively expriring whatever is here.

- RedirectCacheHandler is something of a special case, handling
  redirects which otherwise would be incredibly expensive.
  Unfortunately, this layer is also the dumbest cacher, and
  does not expire anything, ever. To 'invalidate' something in
  this cache, the entire cache needs to be nuked. It may be
  worthwhile to consider moving this to redis instead.

- http-replicator provides an underlying caching layer which
  is HTTP1.1 compliant.

"""

from __future__ import print_function

from .config import NETWORK_PROXY_TYPE
from .config import NETWORK_PROXY_IP
from .config import NETWORK_PROXY_PORT
from .config import NETWORK_PROXY_USER
from .config import NETWORK_PROXY_PASS

from .config import ENABLE_REDIRECT_CACHING

from .config import TRY_REPLICATOR_CACHE_FIRST
from .config import REPLICATOR_PROXY_TYPE
from .config import REPLICATOR_PROXY_IP
from .config import REPLICATOR_PROXY_PORT
from .config import REPLICATOR_PROXY_USER
from .config import REPLICATOR_PROXY_PASS

from .config import INSTANCE_CACHE

from bs4 import BeautifulSoup

from six.moves.urllib.request import HTTPRedirectHandler
from six.moves.urllib.request import ProxyHandler
from six.moves.urllib.request import HTTPPasswordMgrWithDefaultRealm
from six.moves.urllib.request import ProxyBasicAuthHandler
from six.moves.urllib.request import build_opener
from six.moves.urllib.error import HTTPError, URLError

import os
import six
import time
import pickle
import atexit
import tempfile
from hashlib import md5

from fs.opener import fsopendir
from fs.utils import movefile
from tendril.utils.fsutils import temp_fs
from tendril.utils import log
logger = log.get_logger(__name__, log.INFO)

WWW_CACHE = os.path.join(INSTANCE_CACHE, 'soupcache')


def strencode(string):
    """
    This function converts unicode strings to ASCII, using python's
    :func:`str.encode`, replacing any unicode characters present in the
    string. Unicode characters which Tendril expects to see in web content
    related to it are specifically replaced first with ASCII characters
    or character sequences which reasonably reproduce the original meanings.

    :param string: unicode string to be encoded.
    :return: ASCII version of the string.

    """
    nstring = ''
    for char in string:
        if char == u'\u00b5':
            char = 'u'
        if char == u'\u00B1':
            char = '+/-'
        nstring += char
    return nstring.encode('ascii', 'replace')


REDIR_CACHE_FILE = os.path.join(INSTANCE_CACHE, 'redirects.p')

try:
    with open(REDIR_CACHE_FILE, "rb") as rdcf:
        redirect_cache = pickle.load(rdcf)
    logger.info('Loaded Redirect Cache from file')
except IOError:
    redirect_cache = {}
    logger.info('Created new Redirect Cache')


def dump_redirect_cache():
    """
    Called during python interpreter shutdown, this function dumps the
    redirect cache to the file system.
    """
    if DUMP_REDIR_CACHE_ON_EXIT:
        with open(REDIR_CACHE_FILE, 'wb') as f:
            pickle.dump(redirect_cache, f, protocol=2)
        logger.info('Dumping Redirect Cache to file')

DUMP_REDIR_CACHE_ON_EXIT = True

if ENABLE_REDIRECT_CACHING is True:
    atexit.register(dump_redirect_cache)


class CachingRedirectHandler(HTTPRedirectHandler):
    """
    This handler modifies the behavior of
    :class:`urllib2.HTTPRedirectHandler`, resulting in a HTTP ``301`` or
    ``302`` status to be included in the ``result``.

    When this handler is attached to a ``urllib2`` opener, if the opening of
    the URL resulted in a redirect via HTTP ``301`` or ``302``, this is
    reported along with the result. This information can be used by the opener
    to maintain a redirect cache.
    """
    def http_error_301(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_301` handler,
        setting the ``result.status`` to ``301`` in case a http ``301`` error
        is encountered.
        """
        result = HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        """
        Wraps the :func:`urllib2.HTTPRedirectHandler.http_error_302` handler,
        setting the ``result.status`` to ``302`` in case a http ``302`` error
        is encountered.
        """
        result = HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def get_actual_url(url):
    if not ENABLE_REDIRECT_CACHING:
        return url
    else:
        while url in redirect_cache.keys():
            url = redirect_cache[url]
        return url


def _test_opener(openr):
    """
    Tests an opener obtained using :func:`urllib2.build_opener` by attempting
    to open Google's homepage. This is used to test internet connectivity.
    """
    try:
        openr.open('http://www.google.com', timeout=5)
        return True
    except URLError:
        return False


def _create_opener():
    """
    Creates an opener for the internet.

    It also attaches the :class:`CachingRedirectHandler` to the opener and
    sets its User-agent to ``Mozilla/5.0``.

    If the Network Proxy settings are set and recognized, it creates the
    opener and attaches the proxy_handler to it. The opener is tested and
    returned if the test passes.

    If the test fails an opener without the proxy settings is created instead
    and is returned instead.
    """
    use_proxy = False
    use_proxy_auth = False
    proxy_handler = None
    proxy_auth_handler = None

    if NETWORK_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = 'http://' + NETWORK_PROXY_IP
        if NETWORK_PROXY_PORT:
            proxyurl += ':' + NETWORK_PROXY_PORT
        proxy_handler = ProxyHandler({NETWORK_PROXY_TYPE: proxyurl})
        if NETWORK_PROXY_USER is not None:
            use_proxy_auth = True
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(
                None, proxyurl, NETWORK_PROXY_USER, NETWORK_PROXY_PASS
            )
            proxy_auth_handler = ProxyBasicAuthHandler(password_mgr)
    if use_proxy:
        if use_proxy_auth:
            openr = build_opener(
                proxy_handler, proxy_auth_handler, CachingRedirectHandler
            )
        else:
            openr = build_opener(
                proxy_handler, CachingRedirectHandler
            )
    else:
        openr = build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    if _test_opener(openr) is True:
        return openr
    openr = build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr

opener = _create_opener()


def _create_replicator_opener():
    """
    Creates an opener for the replicator.

    It also attaches the :class:`CachingRedirectHandler` to the opener and
    sets its User-agent to ``Mozilla/5.0``.

    If the Network Proxy settings are set and recognized, it creates the
    opener and attaches the proxy_handler to it, and is returned.
    """

    use_proxy = False
    use_proxy_auth = False
    proxy_handler = None
    proxy_auth_handler = None

    if REPLICATOR_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = 'http://' + REPLICATOR_PROXY_IP
        if REPLICATOR_PROXY_PORT:
            proxyurl += ':' + REPLICATOR_PROXY_PORT
        proxy_handler = ProxyHandler(
            {REPLICATOR_PROXY_TYPE: proxyurl}
        )
        if REPLICATOR_PROXY_USER is not None:
            use_proxy_auth = True
            password_mgr = HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(
                None, proxyurl, REPLICATOR_PROXY_USER, REPLICATOR_PROXY_PASS
            )
            proxy_auth_handler = ProxyBasicAuthHandler(password_mgr)
    if use_proxy:
        if use_proxy_auth:
            openr = build_opener(
                proxy_handler, proxy_auth_handler, CachingRedirectHandler
            )
        else:
            openr = build_opener(
                proxy_handler, CachingRedirectHandler
            )
    else:
        openr = build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr


if TRY_REPLICATOR_CACHE_FIRST is True:
    replicator_opener = _create_replicator_opener()


def urlopen(url):
    """
    Opens a url specified by the ``url`` parameter.

    This function handles :
        - Redirect caching, if enabled.
        - Trying the replicator first, if enabled.
        - Retries upto 5 times if it encounters a http ``500`` error.

    """
    retries = 5
    url = get_actual_url(url)
    if TRY_REPLICATOR_CACHE_FIRST is True:
        try:
            page = replicator_opener.open(url)
            try:
                if ENABLE_REDIRECT_CACHING is True and page.status == 301:
                    logger.debug('Detected New Permanent Redirect:\n' +
                                 url + '\n' + page.url)
                    redirect_cache[url] = page.url
            except AttributeError:
                pass
            return page
        except HTTPError as e:
            logger.error("HTTP Error : " + str(e.code) + str(url))
            if e.code == 500:
                time.sleep(0.5)
                retries -= 1
            else:
                raise
        except URLError as e:
            logger.error("URL Error : " + str(e.errno) + " " + str(e.reason))
            raise

    while retries > 0:
        try:
            page = opener.open(url)
            try:
                if ENABLE_REDIRECT_CACHING is True and page.status == 301:
                    logger.debug('Detected New Permanent Redirect:\n' +
                                 url + '\n' + page.url)
                    redirect_cache[url] = page.url
            except AttributeError:
                pass
            return page
        except HTTPError as e:
            logger.error("HTTP Error : " + str(e.code) + str(url))
            if e.code == 500:
                time.sleep(0.5)
                retries -= 1
            else:
                raise
        except URLError as e:
            logger.error("URL Error : " + str(e.errno) + " " + str(e.reason))
            raise
    return None


class WWWCachedFetcher:
    # TODO improve this to use / provide a decent caching layer.
    """
    This class implements a simple filesystem cache which
    can be used to create and obtain from cached www requests.

    The cache is stored in the ``cache_fs`` filesystem, with
    a filename constructed from the md5 sum of the url (encoded as
    ``utf-8`` if necessary).
    """

    def __init__(self, cache_dir=WWW_CACHE):
        self.cache_fs = fsopendir(cache_dir)

    def fetch(self, url, max_age=500000):
        # Use MD5 hash of the URL as the filename
        if six.PY3 or (six.PY2 and isinstance(url, unicode)):
            filepath = md5(url.encode('utf-8')).hexdigest()
        else:
            filepath = md5(url).hexdigest()
        if self.cache_fs.exists(filepath):
            # TODO This seriously needs cleaning up.
            if int(time.time()) - int(time.mktime(self.cache_fs.getinfo(filepath)['modified_time'].timetuple())) < max_age:  # noqa
                return self.cache_fs.open(filepath).read()
        # Retrieve over HTTP and cache, using rename to avoid collisions
        data = urlopen(url).read()
        fd, temppath = tempfile.mkstemp()
        fp = os.fdopen(fd, 'wb')
        fp.write(data)
        fp.close()
        # This can be pretty expensive if the move is across a real filesystem
        # boundary. We should instead use a temporary file in the cache_fs
        # itself
        movefile(temp_fs, temp_fs.unsyspath(temppath),
                 self.cache_fs, filepath)
        return data

#: The module's :class:`WWWCachedFetcher` instance which should be
#: used whenever cached results are desired.
cached_fetcher = WWWCachedFetcher()


def get_soup(url):
    """
    Gets a :mod:`bs4` parsed soup for the ``url`` specified by the parameter.
    The :mod:`lxml` parser is used.

    This function returns a soup constructed of the cached page if one
    exists and is valid, or obtains one and dumps it into the cache if it
    doesn't.
    """
    page = cached_fetcher.fetch(url)
    if page is None:
        return None
    soup = BeautifulSoup(page, 'lxml')
    return soup
