

User Installation
=================

This documents the installation process for setting up Tendril on a user's machine, given
that a Tendril Deployment already exists for the context in which the user will use it. If you
don't already have a Tendril Deployment for your organization, you should look at the Instance
Deployment documentation first.

For the moment, tendril is not designed to be installed to the system (/usr, /opt, etc). Such
installation scripts may be developed for later versions.

Setting up Tendril is essentially a matter of cloning/checking out the approriate git/svn repository
and providing the software with a suitable environment which contains all the necessary dependencies.
The instructions listed here are for Ubuntu, and should work as-is on most Debian based Linux distributions.

The use of ``pyenv`` and ``virtualenv`` for this is strongly recommended but not necessary. The use of these
tools should create a reasonably stable environment until any cross-version kinks are found and worked out.

Compatibility of the scripts has not been tested with any python version other than the ``Python 2.7.6``
which comes with ``Ubuntu 14.04.1 LTS Trusty Tahr``. They will most certainly not work with ``Python 3.x``
in their current form and may or may not work with older point realeases of ``Python 2.7``. While they
may work, it's probably a good idea to avoid using Python versions < 2.7 with these scripts unit a full set
of unit tests can be prepared and run.


Basic Installation
******************

Setting up pyenv
----------------

``pyenv`` is needed to easily set up multiple python versions on your computer. While not strictly
necessary to run Tendril, this is a very strongly recommended step. It allows the following :

 - Make sure Tendril is run with the correct python version.
 - Run tox tests for any developed code (not yet added).

See `<http://davebehnke.com/python-pyenv-ubuntu.html>`_ for a more detailed explanation.

 1. Install Git:

        ``sudo apt-get install git-core curl``

 3. Setup proxy, if any:

        .. code-block:: bash

            export http_proxy=http://user:pass@192.168.1.254:3128
            export https_proxy=http://user:pass@192.168.1.254:3128
            export ftp_proxy=http://user:pass@192.168.1.254:3128

 4. Tell ``git`` to use ``https://`` instead of ``git://`` to get around proxy issues:

        ``git config --global url."https://".insteadOf git://``

 5. Run the installer:

        .. code-block:: bash

            curl -L \
            https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer \
            | bash

 6. Insert the following at the end of ``~/.bashrc``:

        .. code-block:: bash

            export PYENV_ROOT="${HOME}/.pyenv"
            if [ -d "${PYENV_ROOT}" ]; then
                export PATH="${PYENV_ROOT}/bin:${PATH}"
                eval "$(pyenv init -)"
            fi

 7. Install Build Dependencies for Python 2.7:

        .. code-block:: bash

            sudo apt-get build-dep python2.7
            sudo apt-get install build-essential wget \
                libreadline-dev libncurses5-dev libssl1.0.0 tk8.5-dev \
                zlib1g-dev liblzma-dev

 8. Install Python 2.7.6:

        Python 2.7.x, where x>=6, should be fine. x<6 is untested. New features were intruduced in 2.7.5, 2.7.6
        that may be necessary for the scripts to run. If system python is 2.7.6 or better, ``pyenv`` isn't
        strictly necessary. However, to standardize the environment in the absense of cross-version testing and
        intelligent installation scripts, the use of a version-specified python version (as opposed to ``system``)
        is recommended.

        .. code-block:: bash

            pyenv install 2.7.6



Getting the Code
----------------

The code can be obtained from the version control system. For users, the specific instance of ``tendril``
applicable to the organization should be checked out from the locally controlled repository. This repository
should be essentially ``read-only`` with a specific set of people administering the installation. Until the
details can be worked out, use the following checkouts:

    1. Get the Organization's fork of tendril core.

        .. code-block:: bash

            git clone git@gitlab.com:<org>/tendril.git

    2. Create a fork of the Organization's instance configuration. For example, clone
       ``gitlab.com/<org>/tendril-instance-<org>.git`` into ``gitlab.com/<username>/tendril-instance-<org>.git``

    2. Get your fork of the tendril instance configuration.

        .. code-block:: bash

            git clone git@gitlab.com:<username>/tendril-instance-<org>.git ~/.tendril


Setting up virtualenv
---------------------
See `<http://simononsoftware.com/virtualenv-tutorial-part-2/>`_ for a more detailed explanation.

 1. Install ``virtualenv`` from the standard repository.

        .. code-block:: bash

            sudo aptitude install python-virtualenv virtualenvwrapper

 2. Create a directory for the virtual environments.

        .. code-block:: bash

            mkdir ~/.virtualenvs

 3. Tell virtualenvwrapper where the folder you just created is. Put it into the bashrc so that you
    don't have to do it every time you restart.

        .. code-block:: bash

            echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc

    Start up a fresh shell.

 4. Create a new ``virtualenv`` with the correct interpreter version. Don't use system packages.

    If ``pyenv`` is controlling the python version,

        .. code-block:: bash

            cd /path/to/tendril/checkout/trunk/
            mkvirtualenv -p `pyenv which python` --no-site-packages tendril

    If you're just using ``system`` python,

        .. code-block:: bash

            mkvirtualenv --no-site-packages tendril

 5. ``mkvirtualenv`` leaves you with the new virtualenv active. To deactivate,

        .. code-block:: bash

            deactivate

    To reactivate the virtualenv, which you should do when running the scripts in a new terminal:

        .. code-block:: bash

            workon tendril


Installing the Dependencies
---------------------------

 1. Install required python libraries (virtualenv should be active):

        .. code-block:: bash

            cd /path/to/tendril/checkout/trunk/
            pip install -r requirements.txt

        .. note::

            At present, ``requirements.txt`` contains all the dependencies of ``tendril``,
            including those not actually necessary to run the code. As such, the virtualenv
            that results is likely to be reasonably heavy (~361M).

            If a leaner installation is required, the dependencies should be pruned to remove
            the packages included for :

                - Generating documentation
                - Testing, Profiling

 2. Install dependencies not covered by ``requirements.txt``

     a. Install ``sofficehelpers``:

            ``sofficehelpers`` is a collection of scripts to deal with ``libreoffice`` documents.
            The libreoffice python interface (``uno``) requires the use of the python bundled into libreoffice,
            and therefore is kept separate from the rest of tendril. There are plenty of other (and simpler) ways
            to achieve the same effect, inculding a number of uno-based scripts to do this. The custom script is
            retained for the moment to maintain a functional base upon which additional functionality can be added
            on as needed. If another solution is to be used instead, appropriate changes should be made
            to :func:`utils.libreoffice.XLFile._make_csv_files` and :func:`utils.libreoffice.XLFile._parse_sscout`.

            1. Install dependencies:

                .. code-block:: bash

                    sudo apt-get install python-uno python-pip3

            2. Install the ``sofficehelpers`` package from PyPi:

                .. code-block:: bash

                    pip3 install sofficehelpers

 3. Install packages required specifically for your instance. Look up your instance-specific
    documentation and configurations to figure out what those are.


Maintaining the Installation
****************************

Updating the Core
-----------------

    .. code-block:: bash

        cd tendril
        git checkout master
        git pull

Updating the Instance Folder
----------------------------

    .. code-block:: bash

        cd ~/.tendril
        git checkout master
        git pull


Contributing to the Instance
****************************

TODO

