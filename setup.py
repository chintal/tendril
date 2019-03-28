
import os
from setuptools import setup, find_packages
import versioneer


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top
# level README file and 2) it's easier to type in the README file than to
# put a raw string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


install_requirements = [
    # Extracted Modules
    'tendril-utils-core>=0.1.8',
    'tendril-utils-www>=0.1.2',
    'tendril-utils-types>=0.1.2',
    'tendril-utils-markdown>=0.1.1',
    'tendril-utils-pdf>=0.1.1',
    'tendril-utils-yaml>=0.1.1',
    'tendril-utils-libreoffice>=0.1.1',
    'tendril-utils-gschem-files>=0.1.1',
    'tendril-utils-db>=0.1.1',
    'tendril-utils-terminal>=0.1.1',
    'tendril-utils-changelog>=0.1.2',
    'tendril-connector-tally>=0.1.3',
    'tendril-conventions-status>=0.1.1',
    'tendril-conventions-electronics>=0.1.1',
    'tendril-costing>=0.1.2',
    'tendril-dox-render>=0.1.4',
    'tendril-dox-labelmaker>=0.1.4',
    'tendril-dox-wallet>=0.1.1',
    'tendril-entities-base>=0.1.1',
    'tendril-prototype-base>=0.1.1',
    'tendril-products>=0.1.2',
    'tendril-validation>=0.1.1',
    'tendril-validation-common>=0.1.1',
    'tendril-devtooling',
    'driver2200087',
    'iec60063',

    # Confirmed Core Dependencies
    'argparse',
    'pillow',
    'idstring',
    'jinja2',
    'svn>=0.3.44',
    'paramiko',
    'future',
    'appenlight-client',
    'pcb-tools',
    'pyhull',
    'cachetools',   # sourcing.vendors.VendorBase._partcache
    'jsonpickle',   # tendril-server-prefab interfaces
    'pika',

    # Flask Dependencies (to be pruned?)
    'jsmin',
    'cssmin',
    'Flask',
    "Flask-Login",
    "Flask-User",
    "Flask-Principal",
    'Flask-Migrate',
    'Flask-Assets',
    'Flask-Analytics',
    'wtforms-components',

    # Perhaps require reconsideration
    'splinter',    # Replace with direct selenium usage
    'versioneer',
    'watchdog',
    'scipy',       # Used for filter coefficients
]

test_requirements = [
    'pytest',
],

setup_requirements = [
    'twine',
    'wheel',
],

doc_requirements = [
    'sphinx',
    'sphinx-rtd-theme',
    'sphinxcontrib-documentedlist',
    'sphinxcontrib-sqlalchemyviz',
    'sphinxcontrib-googleanalytics',
    'sphinx-argparse',
    'versioneer'
]

script_entry_points = [
    'tendril-gendox = tendril.scripts.gendox:main',
    'tendril-getdox = tendril.scripts.getdox:main',
    'tendril-writecalib = tendril.scripts.writecalib:main',
    'tendril-runtest = tendril.scripts.runtest:main',
    'tendril-testresult = tendril.scripts.testresult:main',
    'tendril-production = tendril.scripts.production:entry_point',
    'tendril-genvmap = tendril.scripts.genvmaps:main',
    'tendril-genvmapaudit = tendril.scripts.genvmapaudits:main',
    'tendril-genpcbpricing = tendril.scripts.genpcbpricing:main',
    'tendril-gsymlib = tendril.scripts.gsymlib:main',
    'tendril-validate = tendril.scripts.validate:main',
]


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
            'frontend/static/gen/*.js',
            'frontend/static/gen/*.css',
            'frontend/static/css/*.css',
            'frontend/static/css/*/*.css',
            'frontend/static/js/*.js',
            'frontend/static/js/*/*.js',
            'frontend/static/images/*.png',
            'frontend/static/images/*.gif',
            'frontend/static/images/*.ico',
            'frontend/static/icons/svgs/*.svg',
            'frontend/static/icons/foundation-icons.*',
            'frontend/templates/*/*.html',
            'frontend/blueprints/*/templates/*.html',
            'frontend/blueprints/*/templates/parts/*.html'
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
    install_requires=install_requirements,
    tests_require=test_requirements,
    setup_requires=setup_requirements,
    extras_require={
        'doc': doc_requirements,
        'test': test_requirements,
        'package': setup_requirements,
    },
    entry_points={
        'console_scripts': script_entry_points
    },
    platforms='any'
)
