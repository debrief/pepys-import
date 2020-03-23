.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/debrief/pepys-import/issues .

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

pepys-import could always use more documentation, whether as part of the
official pepys-import docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/debrief/pepys-import/issues .

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Contributions are always welcome :)

Code coverage
-------------

We're aiming for 100% code coverage on the project, track our progress
here: |code_cov|

.. |code_cov| image:: https://codecov.io/gh/debrief/pepys-import/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/debrief/pepys-import/branch/develop

Upstream security
-----------------

We have continuous vulnerability testing on the Open Source libraries
we depend upon for development: |dev_req| and production: |plain_req|

.. |plain_req| image:: https://snyk.io/test/github/debrief/pepys-import/badge.svg?targetFile=requirements.txt
   :target: https://snyk.io/test/github/debrief/pepys-import?targetFile=requirements.txt

.. |dev_req| image:: https://snyk.io/test/github/debrief/pepys-import/badge.svg?targetFile=requirements_dev.txt
   :target: https://snyk.io/test/github/debrief/pepys-import?targetFile=requirements_dev.txt

Code Style
----------
Black is used on the project: |black|

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
 :target: https://github.com/python/black

It is suggested to install a pre-commit hook in order to apply Black before pushing commits::

    $ pip install pre-commit
    $ pre-commit install


Windows-specific pre-commit instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are some minor issues with the pre-commit library on Windows. If you run into errors Installing
the pre-commit hook, the follow the instructions at `this Github issue <https://github.com/pre-commit/pre-commit/issues/891>`_,
by loading a Command Prompt with administrator permissions and running::

    $ pre-commit clean
    $ pre-commit run black --all-files