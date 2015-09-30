

Instance Deployment
===================

If your organization already has a Tendril deployment, you should skip this
section and go directly to the User Installation section.

Instance deployment is the process you would have to go through to set up a
Tendril instance for your organization, which will then provide the sandbox
within which you can modify Tendril to suit your needs.

Creating an Instance
********************

Instance Components
-------------------

A tendril instance is a combination of atleast two elements:

 - The tendril core, containing the bulk of the business logic
   of tendril.
 - An instance folder, containing all of your propietary
   information, and (eventually) your process workflows.

In addition, various other resources will have to be setup, including:

 - An ``apache2`` server with the following modules :

    - ``mpm_prefork`` (recommended)
    - ``modwsgi``
    - ``modxsendfile``

 - A ``postgresql`` database server. No other database is slated to be supported.

 - The following 'filesystems', each of which is currently expected to be a folder
   on the server running your central Tendril instance :

    - ``docstore`` to store numbered, generated documentation. Typically,
      things like reports, orders, and so on go here.
    - ``refdocs`` to store all Reference documentation.
    - ``wallet`` to store a small collection of standard company documents.

 - Your ``projects`` hierarchy, presently expected to be a tree of SVN checkouts.

Forking Tendril
---------------

While tendril is developed with the goal of having a process-agnostic core,
it may well take some time to achieve the kind of separation that is desired.
For the moment, every Tendril Deployment is expected to be a fork of tendril,
not just a clone. This lets you make whatever changes you need to the core to
get it to function exactly the way you need it to.

The primary tendril repository you should fork is at
https://github.com/chintal/tendril . You should have an (empty) git
repository into which you're going to put the fork. Lets say you're going to
maintain this as a private repository on gitlab, under a group called <org>.

An additional repository, https://github.com/chintal/tendril-frontend-static ,
contains the static files used by the web frontend. This is used as a submodule
inside the core tendril repository. If you want to customize the look and feel
of the frontend, you will likely need to fork this repository as well. The
documentation here does not explain how you would go about doing that. The eventual
goal is to reintegrate the submodule after a package manager is used to remove
the various javascript dependencies from the frontend repository, making it small
enough to be contained within the main repository.

 1. Create a checkout of your empty repository.

    .. code-block:: bash

        git clone git@gitlab.com:<org>/tendril.git

 2. Create a file and commit inside this checkout to create a ``master``
    branch. (There is most definitely a cleaner way to do this, but I haven't
    quite figured out how.)

    .. code-block:: bash

        touch seed
        git add seed
        git commit -m "Initial seed commit"


 2. Add a new ``remote`` pointing to the upstream repository, fetch, and merge.

    .. code-block:: bash

        git remote add upstream https://github.com/chintal/tendril.git
        git fetch upstream
        git checkout -b upstream-master upstream/master
        git checkout master
        git merge upstream-master master

 3. Clone the submodules as well.

    .. code-block:: bash

        git submodule update --init

 4. Get rid of the seed file. (There is most definitely a cleaner way to do this
    as well.)

    .. code-block:: bash

        git log
        git revert <ref for the seed commit>

 5. Push the repository up to gitlab.

    .. code-block:: bash

        git push origin master


The fork thus created is what you you would use as the tendril core within
your organization. You should then follow the instructions in the User
Installation section to set up your central Tendril installation,
configuring the instance folder while you do.

Setting up the Instance Folder
------------------------------

TODO

Generating the Documentation
----------------------------

You should build a copy of the documentation for local use. Your tendril
instance's frontend will serve this documentation to your users.

    .. code-block:: bash

        cd tendril/doc
        make dirhtml

Setting up the 'Filesystems'
----------------------------

Create the local folders to store your ``docstore``, ``refdocs``, and ``wallet``.
Each of these 'filesystems' is used by tendril via ``pyfilesystem`` (:mod:`fs`),
and can in principle be remote filesystems. For your central instance, though, only
using them as local folders is supported at present.

    .. code-block:: bash

        mkdir ~/fs
        mkdir ~/fs/wallet
        mkdir ~/fs/docstore
        mkdir ~/fs/refdocs

    .. seealso::

        These folders can be wherever you want them to be. Just make sure to set
        the following configuration options in your local config overrides :

            - DOCUMENT_WALLET_ROOT
            - DOCSTORE_ROOT
            - REFDOC_ROOT

        Your instance_config itself would benefit from having the reference to
        the XML-RPC endpoint for the filesystem, allowing your users to connect
        directly to it. See the next section for details.

    .. hint::

        Using a remote filesystem instead basically requires the serving of
        files by your webserver (through :mod:`tendril.frontend.blueprints.expose`
        via ``x-sendfile``) to be changed to allow this. You could, in
        principle, mount the remote filesystems locally with :mod:`fs.mountfs`.
        However, expect a considerable performance hit. The ideal route would
        probably be to have :mod:`tendril.frontend.blueprints.expose` redirect
        you to the correct URL of the remote resource instead.

Exposing the Filesystems over http via XML-RPC
----------------------------------------------

TODO

Setting up Apache
-----------------

You can use ``apache`` or the webserver of your choice to serve Tendril. The
basic requirements for the webserver are :

    - Support ``wsgi``
    - (Recommended) Support ``x-sendfile``

    .. hint::

        ``x-sendfile`` is enabled by default. If you want to disable it,
        set ``USE_X_SENDFILE`` to ``False`` in your ``instance_config.py``.

You should edit the ``tendril.wsgi`` file in your instance root as well,
and set the correct path to the ``virtualenv`` you have setup for ``tendril``.
If the ``tendril.wsgi`` file is missing, you should either copy ``tendril.wsgi.sample``
file, if there is one, or you can copy the example below.

Example ``tendril.wsgi``:

    .. literalinclude:: ../sample/tendril.wsgi.sample

Your webserver should also be configured to serve files from within the
exposed filesystems, and the wsgi script should be mounted.

Example configuration for apache:

    .. literalinclude:: ../sample/apache2.tendril.conf.sample

Your webserver should also have the necessary permissions to read/write all
required files (Draft) ::

    (rw) ~/fs
    (r ) ~/tendril
    (r ) ~/.tendril
    (rw) ~/.tendril/cache

This is probably most easily achieved by letting ``wsgi`` run tendril as
the tendril user.

Setting up Postgresql
---------------------

TODO


Maintaining the Instance
************************

TODO

Updating the Core
-----------------

The core would only be updated from upstream by an instance administrator. Updating the
core, especially in the present nascent state of the code (and consequently the API), is
very liable to break things.

The update should be run in a clone of your instance core. Assuming you're using the same
clone as you did to create the fork to begin with, you already have the ``upstream`` remote
setup and the ``upstream-master`` tracking branch.

 1. Fetch updates from upstream and merge into your remote tracking branch :

    .. code-block:: bash

        git checkout upstream-master
        git pull

 2. Merge ``upstream-master`` into your ``master``. If you have customizations in place, you
    should probably merge first into a temporary branch of your ``master`` and make sure nothing
    breaks.

    .. code-block:: bash

        git checkout master
        git merge upstream-master

    .. hint:: This is a good place to run a full test suite and make sure nothing broke.

 3. Push the updates to your central core repository.

    .. code-block:: bash

        git push


Contributing to Upstream
************************

TODO
