

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

 1. Install Git:

        ``sudo apt-get install git-core curl``

 3. Setup proxy, if any:

        .. code-block:: bash

            export http_proxy=http://user:pass@192.168.1.254:3128
            export https_proxy=http://user:pass@192.168.1.254:3128
            export ftp_proxy=http://user:pass@192.168.1.254:3128

 4. (Proxy) Setup corkscrew to use git through a http proxy, if necessary:

        TODO

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

    1. Create an ssh key for yourself, if you don't already have one.

        .. code-block:: bash

            ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

    2. Register the key (``~/.ssh/id_rsa.pub``) on gitlab.

    3. (Proxy) Setup ssh to use corkscrew for the git host, if necessary. Put the following
    into ``~/.ssh/config``, create the file if necessary. Your proxy credentials go into
    ``~/.ssh/proxyauth`` in the format ``user:pass``.

        .. code-block:: bash

            Host gitlab.com
                Hostname gitlab.com
                User git
                IdentityFile ~/.ssh/id_rsa
                ProxyCommand corkscrew proxy.host port %h %p ~/.ssh/proxyauth

    1. Get the Organization's fork of tendril core.

        .. code-block:: bash

            git clone git@gitlab.com:<org>/tendril.git

    2. Create a fork of the Organization's instance configuration. For example, clone
       ``gitlab.com/<org>/tendril-instance-<org>.git`` into ``gitlab.com/<username>/tendril-instance-<org>.git``

    2. Get a clone of your fork of the Organization's instance configuration.

        .. code-block:: bash

            git clone git@gitlab.com:<username>/tendril-instance-<org>.git ~/.tendril


Setting up virtualenv
---------------------
See `<http://www.simononsoftware.com/virtualenv-tutorial-part-2/>`_ for a more detailed explanation.

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

 6. If you've installed ``pyenv``, you can use the following commands instead to setup and
    use your virtualenv:

        .. code-block:: bash

            pyenv virtualenv 2.7.6 tendril
            pyenv activate tendril
            pyenv deactivate

Installing the Dependencies
---------------------------

 1. Install required python libraries (virtualenv should be active):

        .. code-block:: bash

            cd /path/to/tendril/clone
            pip install -e .

        .. hint::

            You can install the package into the virtualenv or even into your
            system if you really want to. However, due to the present volatile
            state of the code, you should expect a fairly continuous stream of
            small changes, most of which aren't going to come with a bump in the
            version number. This may make upgrading the package a more involved
            process. This command installs all the dependencies normally, but the
            tendril package itself redirects to the clone, where you can make
            changes which instantly propagate to the version you get when you
            ``import tendril``.

        .. hint::

            The dependencies may require additional libraries (and their
            development headers) to be installed on your system. A non-exhaustive
            list of the libraries you should have available is :

              - freetype
              - libpng
              - libffi
              - libpqxx (postgresql)

 2. Install dependencies not covered by ``requirements.txt``

     a. Install ``sofficehelpers``:

            ``sofficehelpers`` is a collection of scripts to deal with ``libreoffice``
            documents. The libreoffice python interface (``uno``) requires use of the
            python bundled into libreoffice, and therefore is kept separate from the
            rest of tendril. There are plenty of other (and simpler) ways to achieve
            the same effect, inculding a number of uno-based scripts to do this. The
            custom script is retained for the moment to maintain a functional base upon
            which additional functionality can be added on as needed. If another solution
            is to be used instead, appropriate changes should be made
            to :func:`utils.libreoffice.XLFile._make_csv_files` and
            :func:`utils.libreoffice.XLFile._parse_sscout`.

            1. Install dependencies:

                .. code-block:: bash

                    sudo apt-get install python-uno python-pip3

            2. Install the ``sofficehelpers`` package from PyPi:

                .. code-block:: bash

                    pip3 install sofficehelpers

     b. (Optional) Install ``gaf 1.9.1`` or the devlopment version from git. This is required
        for ``gaf export``, which in turn is required to convert ``gschem`` files to pdf on
        a headless server. Refer to your instance specific conventions and rules to determine
        if using this version generally is safe.

            .. code-block:: bash

                wget http://ftp.geda-project.org/geda-gaf/unstable/v1.9/1.9.1/geda-gaf-1.9.1.tar.gz
                tar xvzf geda-gaf-1.9.1.tar.gz
                cd geda-gaf-1.9.1
                ./configure --prefix=/opt/geda
                make
                make install

            .. seealso::::

                The following config options in your instance config may need to be tweaked to
                use this version of gEDA/gaf :

                  - GEDA_SCHEME_DIR = "/opt/geda/share/gEDA/scheme"
                  - USE_SYSTEM_GAF_BIN = False
                  - GAF_BIN_ROOT = "/opt/geda/bin"
                  - GAF_ROOT = os.path.join(USER_HOME, 'gEDA2')
                  - GEDA_SYMLIB_ROOT = os.path.join(GAF_ROOT, 'symbols')


 3. Install packages required specifically for your instance. Look up your instance-specific
    documentation and configurations to figure out what those are.

 4. Setup your repository tree. This tree need not be specially created for tendril. You can
    point to a folder within which all your repositories exist. The following are the
    constraints you should keep in mind :

        - Any folder with a ``configs.yaml`` in the correct format is assumed to be a
          gEDA project, and the correct folder structure around it is expected.

        - Most workflows call for specific information stored in a specific location
          in the repository tree, such as inventory information, for instance. These
          resources should mirror their location (relative to the repository root) in
          the canonical repository tree.

    Beyond this, you can use whatever method or tool you desire to keep the repositories
    up to date. I recommend `checkoutmanager <https://github.com/reinout/checkoutmanager>`.

    a. Install ``checkoutmanager``

        .. code-block:: bash

            pip install checkoutmanager

    b. Setup your ``~/.checkoutmanager.cfg``. Your instance may have a sample in the
       ``resources`` folder. If it does, you may be able to simply copy the configuration
       and make whatever local changes you require.

        .. code-block:: bash

            cd ~/.tendril/resources
            cp checkoutmanager.cfg ~/.checkoutmanager.cfg

    c. Create the checkouts.

        .. code-block:: bash

            checkoutmanager co

 5. (Optional) Create a 'full' local tendril installation, detaching your copy from requiring
    the central tendril installation to be accessible on the network.

        .. warning:: Real synchronization is not implemented yet. While some parts of tendril
                     are to safe to use in isolation, much of it is not. Use with extreme caution.
                     The following is a non-exhaustive list of potential failures :

                         - ``postgresql`` replication / synchronization is not set up. Anything
                           that hits the database is likely to fail.

                         - Filesystem synchronization is not setup. Anything that hits ``docstore``
                           is likely to cause trouble. ``refdocs`` and ``wallet`` are relatively
                           safe to have a local version of the filesystem of, though you should
                           remember that these are copies of the respective filestsyem - which
                           you will have to maintain yourself.

    Follow the instructions in the Instance Deployment section to :

        - Setup ``apache``.
        - Setup the filesystems.
        - Generate your copy of ``refdocs``.


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

