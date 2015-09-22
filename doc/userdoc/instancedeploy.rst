

Instance Deployment
===================

If your organization already has a Tendril deployment, you should skip this
section and go directly to the User Installation section.

Instance deployment is the process you would have to go through to set up a
Tendril instance for your organization, which will then provide the sandbox
within which you can modify Tendril to suit your needs.

Instance Components
*******************

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
***************

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

        https://github.com/chintal/tendril.git
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
your organization. If you implement new functionality within tendril, you are
welcome to keep it to yourself (subject to the terms of the licenses of the
files involved in your change). You are, of course, encouraged to send
the changes over for integration into public tendril core, either in the form
of patches or as a pull request on github.


Setting up the Instance Folder
******************************

TODO


