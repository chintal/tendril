#!/usr/bin/env python

import os
from setuptools import setup, find_packages
import versioneer


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top
# level README file and 2) it's easier to type in the README file than to
# put a raw string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="tendril-framework",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Chintalagiri Shashank",
    author_email="shashank@chintal.in",
    description='An open-ended framework for handling information, to aid '
                'development, management, and production cycles',
    license="AGPLv3",
    keywords="",
    url="https://github.com/chintal/tendril",
    package_dir={'tendril': 'tendril'},
    packages=find_packages(exclude=['profiling', 'contrib', 'doc', 'tests*']),
    include_package_data=True,
    package_data={
        'tendril': [
            # gedaif module
            'gedaif/templates/*.yaml',
            # dox module
            'dox/templates/*.tex',
            'dox/templates/*/*.tex',
            # frontend module
            'frontend/static/*',
            'frontend/templates/*/*.html',
            'frontend/blueprints/*/templates/*.html',
        ]
    },
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: "
        "Electronic Design Automation (EDA)",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "License :: OSI Approved :: "
        "GNU Affero General Public License v3 or later (AGPLv3+)",
        "Framework :: Flask",
        "Framework :: Twisted",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        # Confirmed Core Dependencies
        'argparse',
        'psycopg2',
        'arrow',
        'pillow',
        'qrcode',
        'beautifulsoup4',
        'PyPDF2',
        'lxml',
        'idstring',
        'jinja2',
        'SQLAlchemy',
        'sqlalchemy_utils',
        'alembic',
        'svn',
        'fs',
        'paramiko',
        'pyyaml',
        'progress',
        'colorama',

        # Flask Dependencies (to be pruned?)
        'jsmin',
        'cssmin',
        'Flask',
        "Flask-Login==0.2.11",
        "Flask-User==0.6.1",
        "Flask-Principal",
        'Flask-Migrate',
        'Flask-Assets',

        # Perhaps require reconsideration
        'matplotlib',  # Pulls in numpy!
        'splinter',    # Replace with direct selenium usage
        'versioneer',

        # Extracted Modules
        'driver2200087',
        'iec60063',
        'tendril-gedaif-sym2eps',
    ],
    tests_require=[
        'pytest',
    ],
    setup_requires=[
        'twine',
        'wheel',
    ],
    extras_require={
        'doc': [
            'sphinx',
            'sphinx-rtd-theme',
            'sphinxcontrib-documentedlist',
            'sphinxcontrib-googleanalytics==0.1.dev20150826',
            'versioneer'
            ]
    },
    platforms='any'
)
