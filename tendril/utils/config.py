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
The Config Module (:mod:`tendril.utils.config`)
===============================================

This module provides the core configuration for Tendril.

The Tendril configuration file is itself a Python file, and is imported
from it's default location (``INSTANCE_ROOT/instance_config.py``, where
INSTANCE_ROOT is ``~/.tendril``). In case this folder needs to be moved
elsewhere, such as when it needs to be run via wsgi using the web server's
user, the INSTANCE_ROOT can be moved by placing a file in the user's
home directory (``~/.tendril/redirect``), containing the path to the
actual instance folder.

The ``instance_config.py`` file is the primary configuration for Tendril.
It is intended to be maintained at an Instance level by the tendril
administrator. Since some parameters may need to be changed per-installation
to adapt it to the user's setup, an additional configuration file can be
added in (``INSTANCE_ROOT/local_config_overrides.py``), containing only those
parameters which the user wishes to override.

When the configuration is parsed during startup, (at the time of the first
import of the config module) this module performs the import using the
:func:`tendril.utils.fsutils.import_` function and the :mod:`imp` module.
Each recognized config option and variable is obtained from the first
location where it is found from the following list of sources:

    - ``local_config_overrides.py``
    - ``instance_config.py``
    - The defaults specified here.

The following constraints should be kept in mind when setting up your
configuration :

    - The configuration files are all python files. You can execute pretty
      much whatever you want within them, as long as the final configuration
      value ends up in the module namespace at the correct variable.
    - The order of the config parameters is somewhat important. The actual
      configuration values can be constructed at run time from
      configurations parameters which already exist in the namespace.
    - The core config module (this one) uses ``eval()`` to execute the
      ``default`` strings. The values in ``instance_config`` and
      ``local_config_overrides``, however, are used as is. As such, each
      option or constant specified in one of those files must be fully
      specified within that file - it can't, for instance, use the
      INSTANCE_ROOT value to construct paths unless it defines it for
      itself.
    - Configuration constants will be set in the instance and local config
      modules. Configuration options will not.

Configuration Options
---------------------

.. documentedlist::
    :listobject: tendril.utils.config.all_config_option_groups
    :header: Option Default Description
    :spantolast:
    :descend:


Configuration Constants
-----------------------

.. documentedlist::
    :listobject: tendril.utils.config.all_config_constant_groups
    :header: Option Default Description
    :spantolast:
    :descend:

"""

from __future__ import print_function

import os
import sys
import inspect
from .fsutils import import_


config_module = sys.modules[__name__]
CONFIG_PATH = os.path.abspath(inspect.getfile(inspect.currentframe()))


class ConfigConstant(object):
    """
    A configuration `constant`. This is fully specified in this
    file and cannot be changed by the user or the instance
    administrator without modifying the core code.

    The value itself is constructed using ``eval()``.
    """
    def __init__(self, name, default, doc):
        self.name = name
        self.default = default
        self.doc = doc

    @property
    def value(self):
        return eval(self.default)


def load_constants(constants):
    """
    Loads the constants in the provided list into the module
    namespace.

    :param constants: list of :class:`ConfigConstant`
    :return: None
    """
    for option in constants:
        setattr(config_module, option.name, option.value)


# def set_config_contants(constants):
#     """
#     Sets the configuration constants in the Instance and Local
#     configuration modules.
#
#     :param constants: list of :class:`ConfigConstant`
#     :return: None
#
#     """
#     global LOCAL_CONFIG
#     global INSTANCE_CONFIG
#
#     for option in constants:
#         setattr(INSTANCE_CONFIG, option.name, option.value)
#         if LOCAL_CONFIG is not None:
#             setattr(LOCAL_CONFIG, option.name, option.value)


config_constants_basic = [
    ConfigConstant(
        'TENDRIL_ROOT',
        'os.path.normpath(os.path.join(CONFIG_PATH, os.pardir, os.pardir))',
        'Path to the tendril package root.'
    ),
    ConfigConstant(
        'INSTANCE_ROOT',
        "os.path.join(os.path.expanduser('~'), '.tendril')",
        "Path to the tendril instance root. Can be redirected if necessary"
        "with a file named ``redirect`` in this folder."
    )
]

load_constants(config_constants_basic)


if os.path.exists(os.path.join(INSTANCE_ROOT, 'redirect')):
    print("Found redirect")
    with open(os.path.join(INSTANCE_ROOT, 'redirect'), 'r') as f:
        INSTANCE_ROOT = f.read().strip()


config_constants_redirected = [
    ConfigConstant(
        'INSTANCE_CONFIG_FILE',
        "os.path.join(INSTANCE_ROOT, 'instance_config.py')",
        'Path to the tendril instance configuration.'
    ),
    ConfigConstant(
        'LOCAL_CONFIG_FILE',
        "os.path.join(INSTANCE_ROOT, 'local_config_overrides.py')",
        'Path to local overrides to the instance configuration.'
    ),
    ConfigConstant(
        # TODO deal with an instance specific templates folder
        'DOX_TEMPLATE_FOLDER',
        "os.path.join(TENDRIL_ROOT, 'dox/templates')",
        "Path to the template folder to use for tendril.dox"
    )
]

load_constants(config_constants_redirected)


INSTANCE_CONFIG = import_(INSTANCE_CONFIG_FILE)
LOCAL_CONFIG = None
if os.path.exists(LOCAL_CONFIG_FILE):
    LOCAL_CONFIG = import_(LOCAL_CONFIG_FILE)

# set_config_contants(config_constants_basic)
# set_config_contants(config_constants_redirected)


class ConfigOption(object):
    """
    A configuration `option`. These options can be overridden
    by specifying them in the ``instance_config`` and
    ``local_config_overrides`` files.

    If specified in one of those files, the value should be
    the actual configuration value and not an expression. The
    default value specified here is used through ``eval()``.

    """
    def __init__(self, name, default, doc):
        self.name = name
        self.default = default
        self.doc = doc

    @property
    def value(self):
        try:
            return getattr(LOCAL_CONFIG, self.name)
        except:
            pass
        try:
            return getattr(INSTANCE_CONFIG, self.name)
        except AttributeError:
            try:
                return eval(self.default)
            except SyntaxError:
                print("Required config option not set in "
                      "instance config : " + self.name)
                raise


def load_config(options):
    """
    Loads the options in the provided list into the module
    namespace.

    :param options: list of :class:`ConfigOption`
    :return: None
    """
    for option in options:
        setattr(config_module, option.name, option.value)


config_options_paths = [
    ConfigOption(
        'AUDIT_PATH',
        "os.path.join(INSTANCE_ROOT, 'manual-audit')",
        "Folder where files generated for manual audit should be stored"
    ),
    ConfigOption(
        'SVN_ROOT',
        "os.path.join(INSTANCE_ROOT, 'projects')",
        "Common ancestor for all VCS checkout folders. While tendril will "
        "try to descend into this folder indefinitely, avoid using overly "
        "generic paths (like '/' or '~') to avoid surprises and preserve "
        "performance."
    ),
    ConfigOption(
        'PROJECTS_ROOT',
        "SVN_ROOT",
        "Common ancestor for all project folders. Use this if your projects"
        "are in a single sub-tree of your VCS_ROOT, for example. \nWhile "
        "tendril will try to descend into this folder indefinitely, avoid "
        "using overly generic paths (like '/' or '~') to avoid surprises "
        "and preserve performance."
    ),
    ConfigOption(
        'INSTANCE_CACHE',
        "os.path.join(INSTANCE_ROOT, 'cache')",
        "Folder within which the tendril instance should store it's cache(s)."
        "Make sure the the users running tendril (as well as the webserver, "
        "if the web frontend is being used) have write access to this folder."
    ),
]

load_config(config_options_paths)


config_options_fs = [
    ConfigOption(
        'DOCUMENT_WALLET_ROOT',
        "os.path.join(INSTANCE_ROOT, 'wallet')",
        "Folder for the document wallet filesystem"
    ),
    ConfigOption(
        'DOCSTORE_ROOT',
        "os.path.join(INSTANCE_ROOT, 'docstore')",
        "Folder for the docstore filesystem"
    ),
    ConfigOption(
        'REFDOC_ROOT',
        "os.path.join(INSTANCE_ROOT, 'refdocs')",
        "Folder for the refdocs filesystem"
    ),
]

load_config(config_options_fs)


config_constants_fs = [
    ConfigConstant(
        'DOCUMENT_WALLET_PREFIX',
        "'wallet'",
        "Prefix for the Document Wallet in the expose hierarchy"
    ),
    ConfigConstant(
        'DOCSTORE_PREFIX',
        "'docstore'",
        "Prefix for the Docstore in the expose hierarchy"
    ),
    ConfigConstant(
        'REFDOC_PREFIX',
        "'refdocs'",
        "Prefix for refdocs in the expose hierarchy"
    ),
]

load_constants(config_constants_fs)
# set_config_contants(config_constants_fs)

config_options_resources = [
    ConfigOption(
        'DOCUMENT_WALLET',
        "{}",
        "Dictionary containing keys and filenames of the documents "
        "in the wallet"
    ),
    ConfigOption(
        "PRINTER_NAME",
        "{}",
        "Name of the printer to use for printing. "
        "Tendril will use 'lp -d PRINTER_NAME to print."
    )
]

load_config(config_options_resources)


config_options_geda = [
    ConfigOption(
        'GEDA_SCHEME_DIR',
        "'/usr/share/gEDA/scheme'",
        "The 'scheme' directory of the gEDA installation to use."
    ),
    ConfigOption(
        "USE_SYSTEM_GAF_BIN",
        "True",
        "Whether to use the gEDA binary located in system PATH. This config "
        "option is present to allow you to switch the gEDA instance tendril "
        "uses from your system default to a manually installed later version."
        "In order to generate schematic PDFs on a headless install, you need "
        "to have a version of gEDA that includes the `gaf` tool."
    ),
    ConfigOption(
        'GAF_BIN_ROOT',
        "None",
        "If system gEDA binaries are not to be used, specify the path to the "
        "'bin' folder where the correct 'gEDA' binaries go."
    ),
    ConfigOption(
        'GAF_ROOT',
        "os.path.join(os.path.expanduser('~'), 'gEDA2')",
        "The path to your gEDA gaf folder (named per the gEDA quickstart "
        "tutorial), within which you have your symbols, footprints, etc. "
    ),
    ConfigOption(
        'GEDA_SYMLIB_ROOT',
        "os.path.join(GAF_ROOT, 'symbols')",
        "The folder containing your gEDA symbols."
    ),
]

load_config(config_options_geda)


config_options_network_caching = [
    ConfigOption(
        'ENABLE_REDIRECT_CACHING',
        "True",
        "Whether or not to cache 301 and 302 redirects."
    ),
    ConfigOption(
        'TRY_REPLICATOR_CACHE_FIRST',
        "False",
        "Whether or not to use the replicator cache"
    ),
]

load_config(config_options_network_caching)


config_options_proxy = [
    ConfigOption(
        'NETWORK_PROXY_TYPE',
        "None",
        "The type of proxy to use. 'http' for squid/http, 'None' for none."
        "No other proxy types presently supported."
    ),
    ConfigOption(
        'NETWORK_PROXY_IP',
        "None",
        "The proxy server IP address."
    ),
    ConfigOption(
        'NETWORK_PROXY_PORT',
        "3128",
        "The proxy server port."
    ),
    ConfigOption(
        'NETWORK_PROXY_USER',
        "None",
        "The username to authenticate with the proxy server."
    ),
    ConfigOption(
        'NETWORK_PROXY_PASS',
        "None",
        "The password to authenticate with the proxy server."
    ),
]

load_config(config_options_proxy)


config_options_repl_proxy = [
    ConfigOption(
        'REPLICATOR_PROXY_TYPE',
        "'http'",
        "The type of replicator proxy to use. 'http' for http-replicator, "
        "'None' for none. No other proxy types presently supported."
    ),
    ConfigOption(
        'REPLICATOR_PROXY_IP',
        "'localhost'",
        "The replicator proxy server IP address."
    ),
    ConfigOption(
        'REPLICATOR_PROXY_PORT',
        "'8080'",
        "The replicator proxy server port."
    ),
    ConfigOption(
        'REPLICATOR_PROXY_USER',
        "None",
        "The username to authenticate with the replicator proxy server."
    ),
    ConfigOption(
        'REPLICATOR_PROXY_PASS',
        "None",
        "The password to authenticate with the replicator proxy server."
    ),
]

load_config(config_options_repl_proxy)


config_options_db = [
    ConfigOption(
        'DATABASE_HOST',
        "None",
        "The database server host."
    ),
    ConfigOption(
        'DATABASE_PORT',
        "5432",
        "The database server port."
    ),
    ConfigOption(
        'DATABASE_USER',
        "None",
        "The username to login to the database server."
    ),
    ConfigOption(
        'DATABASE_PASS',
        "None",
        "The password to login to the database server."
    ),
    ConfigOption(
        'DATABASE_DB',
        "None",
        "The name of the database."
    ),
]

load_config(config_options_db)


def build_db_uri(dbhost, dbport, dbuser, dbpass, dbname):
    """
    Builds a ``postgresql`` DB URI from the parameters provided.

    :param dbhost: Hostname / IP of the database server
    :param dbport: Port of the database server
    :param dbuser: Username of the database user
    :param dbpass: Password of the database user
    :param dbname: Name of the database
    :return: The DB URI
    """
    return 'postgresql://' + \
        dbuser + ":" + dbpass + "@" + dbhost + ':' + dbport + '/' + dbname


DB_URI = build_db_uri(DATABASE_HOST, DATABASE_PORT,
                      DATABASE_USER, DATABASE_PASS,
                      DATABASE_DB)


config_options_frontend = [
    ConfigOption(
        'USE_X_SENDFILE',
        "True",
        "Whether to use X-SENDFILE to send files from the web frontend. "
        "Note that your web server must also support and be configured "
        "to do this."
    ),
]

load_config(config_options_frontend)


config_options_mail = [
    ConfigOption(
        'MAIL_USERNAME',
        "None",
        "The username to authenticate with the SMTP server"
    ),
    ConfigOption(
        'MAIL_PASSWORD',
        "None",
        "The password to authenticate with the SMTP server"
    ),
    ConfigOption(
        'MAIL_DEFAULT_SENDER',
        "None",
        "The sender to use when sending emails"
    ),
    ConfigOption(
        'MAIL_SERVER',
        "None",
        "The host of the SMTP server to use"
    ),
    ConfigOption(
        'MAIL_PORT',
        "None",
        "The port of the SMTP server to use"
    ),
    ConfigOption(
        'MAIL_PORT',
        "587",
        "The port of the SMTP server to use"
    ),
    ConfigOption(
        'MAIL_USE_SSL',
        "True",
        "Whether to use SSL when sending emails"
    ),
    ConfigOption(
        'MAIL_USE_TLS',
        "False",
        "Whether to use TLS when sending emails"
    )
]

load_config(config_options_mail)


config_options_security = [
    ConfigOption(
        'ADMIN_USERNAME',
        "None",
        "The username for the first Admin user"
    ),
    ConfigOption(
        'ADMIN_FULLNAME',
        "None",
        "The full name for the first Admin user"
    ),
    ConfigOption(
        'ADMIN_EMAIL',
        "None",
        "The e-mail for the first Admin user"
    ),
    ConfigOption(
        # TODO This is essentially public. Fix that.
        'ADMIN_PASSWORD',
        "None",
        "The password for the first Admin user"
    ),
    ConfigOption(
        # TODO This is essentially public. Fix that.
        'SECRET_KEY',
        "None",
        "The secret key for the frontend authentication system"
    )
]

load_config(config_options_security)


config_options_currency = [
    ConfigOption(
        'BASE_CURRENCY',
        "INR",
        "The code for the base currency."
    ),
    ConfigOption(
        'BASE_CURRENCY_SYMBOL',
        "INR ",
        "The symbol for the base currency."
    ),
]

load_config(config_options_currency)


config_options_company = [
    ConfigOption(
        'COMPANY_NAME',
        "None",
        "The full name of the company"
    ),
    ConfigOption(
        'COMPANY_NAME_SHORT',
        "COMPANY_NAME",
        "A shortened name for the company"
    ),
    ConfigOption(
        'COMPANY_EMAIL',
        "MAIL_DEFAULT_SENDER",
        "The company email address"
    ),
    ConfigOption(
        'COMPANY_ADDRESS_LINE',
        "None",
        "The company address, in a single line"
    ),
    ConfigOption(
        'COMPANY_LOGO_PATH',
        "None",
        "The path to the company logo, relative to INSTANCE_ROOT"
    ),
    ConfigOption(
        'COMPANY_BLACK_LOGO_PATH',
        "None",
        "The path to the company logo for use on a black background, "
        "relative to INSTANCE_ROOT"
    ),
    ConfigOption(
        'COMPANY_PO_LCO_PATH',
        "None",
        "The path to the company lco file for use with latex scrlttr2, "
        "relative to INSTANCE_ROOT"
    ),
    ConfigOption(
        'COMPANY_GOVT_POINT',
        "None",
        "The name of the person who signs documents "
        "outbound to the government"
    ),
    ConfigOption(
        'COMPANY_PO_POINT',
        "None",
        "The name of the person who signs documents "
        "outbound to vendors"
    ),
    ConfigOption(
        'COMPANY_IEC',
        "None",
        "The company import-exchange code"
    ),
]

load_config(config_options_company)


config_options_inventory = [
    ConfigOption(
        'INVENTORY_LOCATIONS',
        "[]",
        "A list of names of inventory locations"
    ),
    ConfigOption(
        'ELECTRONICS_INVENTORY_DATA',
        "[]",
        "A list of dictionaries specifying the locations and formats of "
        "inventory data."
    ),
]

load_config(config_options_inventory)


config_options_vendors = [
    ConfigOption(
        'VENDOR_MAP_AUDIT_FOLDER',
        "os.path.join(AUDIT_PATH, 'vendor-maps')",
        "The folder in which the vendor maps audits should be stored"
    ),
    ConfigOption(
        'PRICELISTVENDORS_FOLDER',
        "os.path.join(INSTANCE_ROOT, 'sourcing', 'pricelists')",
        "The folder in which the price lists for pricelist vendors "
        "are located."
    ),
    ConfigOption(
        'CUSTOMSDEFAULTS_FOLDER',
        "os.path.join(INSTANCE_ROOT, 'sourcing', 'customs')",
        "The folder in which customs defaults are located."
    ),
    ConfigOption(
        'VENDORS_DATA',
        "[]",
        "A list of dictionaries containing vendor details, one for each"
        "configured vendor."
    ),
]

load_config(config_options_vendors)


def doc_render(group):
    """
    Converts a list of :class:`ConfigOption` or :class:`ConfigConstant`
    into a list compatible with :mod:`sphinxcontrib.documentedlist` for
    generating the configuration parameter documentation.
    """
    return [[x.name, x.default, x.doc] for x in group]


all_config_option_groups = [
    [doc_render(config_options_paths),
     "Options to configure paths for various local resources"],
    [doc_render(config_options_fs),
     "Options to configure the 'filesystems' containing instance resources"],
    [doc_render(config_options_resources),
     "Options to configure details of various instance resources"],
    [doc_render(config_options_geda),
     "Options to configure the gEDA installation and related resources"],
    [doc_render(config_options_network_caching),
     "Options to configure network caching behavior"],
    [doc_render(config_options_proxy),
     "Options to configure a network proxy"],
    [doc_render(config_options_repl_proxy),
     "Options to configure a replicator proxy"],
    [doc_render(config_options_db),
     "Options to configure the instance database"],
    [doc_render(config_options_frontend),
     "Options to configure the frontend"],
    [doc_render(config_options_mail),
     "Options to configure e-mail"],
    [doc_render(config_options_security),
     "Options to configure security features"],
    [doc_render(config_options_company),
     "Options to configure company details"],
    [doc_render(config_options_inventory),
     "Options to configure inventory details"],
    [doc_render(config_options_vendors),
     "Options to configure vendor details"]
]


all_config_constant_groups = [
    [doc_render(config_constants_basic),
     "Basic config constants"],
    [doc_render(config_constants_redirected),
     "Configuration constants, following INSTANCE_ROOT redirection if needed"],
    [doc_render(config_constants_fs),
     "Filesystems related constants"]
]
