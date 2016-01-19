

Overview
--------

Functionality will almost always be implemented and exposed in the following
sequence :

    - As Python code, which can be used from ipython or other python
      shells. This form of use represents the lowest level access to
      Tendril.
    - Commonly used functionality which can be packaged into a specific
      set of actions are implemented as CLI scripts.
      See :mod:`tendril.scripts`.
    - Functionality which is to be used by a larger set of people and
      therefore including some form of user authentication is finally
      implemented in the frontend for use from a web browser.
      See :mod:`tendril.frontend`.
