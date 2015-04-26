"""
WWW Utils Module Documentation (:mod:`utils.wwwutils`)
======================================================
"""

from utils import log
logger = log.get_logger(__name__, log.INFO)

from config import NETWORK_PROXY_TYPE
from config import NETWORK_PROXY_IP
from config import NETWORK_PROXY_PORT
from config import NETWORK_PROXY_USER
from config import NETWORK_PROXY_PASS

from config import KOALA_ROOT
from config import ENABLE_REDIRECT_CACHING

from bs4 import BeautifulSoup
import urllib2

import time
import pickle
import atexit
import os


def strencode(string):
    nstring = ''
    for char in string:
        if char == u'\u00b5':
            char = 'u'
        nstring += char
    return nstring.encode('ascii', 'replace')


REDIR_CACHE_FILE = os.path.join(KOALA_ROOT, 'utils', 'redirects.p')

try:
    with open(REDIR_CACHE_FILE, "rb") as rdcf:
        redirect_cache = pickle.load(rdcf)
    logger.info('Loaded Redirect Cache from file')
except IOError:
    redirect_cache = {}
    logger.info('Created new Redirect Cache')


def dump_redirect_cache():
    with open(REDIR_CACHE_FILE, 'wb') as f:
        pickle.dump(redirect_cache, f)
    logger.info('Dumping Redirect Cache to file')

if ENABLE_REDIRECT_CACHING is True:
    atexit.register(dump_redirect_cache)


class CachingRedirectHandler(urllib2.HTTPRedirectHandler):

    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def _test_opener(openr):
    try:
        openr.open('http://www.google.com', timeout=5)
        return True
    except urllib2.URLError:
        return False


def _create_opener():
    use_proxy = False
    use_proxy_auth = False
    proxy_handler = None
    proxy_auth_handler = None

    if NETWORK_PROXY_TYPE == 'http':
        use_proxy = True
        proxyurl = 'http://' + NETWORK_PROXY_IP
        if NETWORK_PROXY_PORT:
            proxyurl += ':' + NETWORK_PROXY_PORT
        proxy_handler = urllib2.ProxyHandler({NETWORK_PROXY_TYPE: proxyurl})
        if NETWORK_PROXY_USER is not None:
            use_proxy_auth = True
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, proxyurl, NETWORK_PROXY_USER, NETWORK_PROXY_PASS)
            proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
    if use_proxy:
        if use_proxy_auth:
            openr = urllib2.build_opener(proxy_handler, proxy_auth_handler, CachingRedirectHandler)
        else:
            openr = urllib2.build_opener(proxy_handler, CachingRedirectHandler)
    else:
        openr = urllib2.build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    if _test_opener(openr) is True:
        return openr
    openr = urllib2.build_opener(CachingRedirectHandler)
    openr.addheaders = [('User-agent', 'Mozilla/5.0')]
    return openr

opener = _create_opener()


def urlopen(url):
    retries = 5
    if ENABLE_REDIRECT_CACHING is True:
        while url in redirect_cache.keys():
            url = redirect_cache[url]
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
        except urllib2.HTTPError, e:
            logger.error("HTTP Error : " + str(e.code) + str(url))
            if e.code == 500:
                time.sleep(0.5)
                retries -= 1
            else:
                retries = 0
        except urllib2.URLError, e:
            logger.error("URL Error : " + str(e.errno) + " " + str(e.reason))
            retries = 0
    return None


def get_soup(url):
    page = urlopen(url)
    if page is None:
        return None
    soup = BeautifulSoup(page, 'lxml')
    return soup

