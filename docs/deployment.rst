Creating a deployable release
=============================

Pepys-import is deployed by providing a zip file to the client containing everything necessary to run
pepys-import on a Windows 10 computer. For instructions on how to install from a deployable zip file,
see  :doc:`the user-focused README <installation>`.

For significant releases, the `pepys-import` version should be incremented,
using::

    bumpversion patch


**Note:** once the version has been incremented, a new entry should be
included in `History.rst`.

There are two ways to create a deployment: either automatically on Github Actions, or manually on a Windows 10 computer.

Automatic deployment
--------------------
1. Merge the :code:`develop` branch into the :code:`master` branch.

2. Create, and push, a tag on the master branch, with a name like :code:`v0.5`.

3. Github Actions will automatically build a deployable zip file, and upload it to a draft release on the Github project.

4. Go to the `Pepys-Import releases page <https://github.com/debrief/pepys-import/releases>`_ and you should see a draft release. Edit
   the release details to include a summary of changes, and publish the release.

**Note:** Deployable releases are also automatically built for every PR, and can be accessed by clicking *Details* next to the
*Create Deployment* check on a PR, and then clicking the *Artifacts* button. This will download a zip file, and *inside* this zip file
will be the Pepys release zip file (ie. a double-zip).


Manual deployment
-----------------
Follow the instructions below on a Windows 10 machine (this *cannot* be done from any other sort of computer):

1. Clone a new copy of the `pepys-import repository <https://github.com/debrief/pepys-import/>`_, and make sure
it is at the relevant commit for the version you want to release (we recommend creating a git tag for the commit
you use as the basis for a release). (**Note:** Do not create a deployable release from a previously-cloned
version of the repository that you have developed in - always clone a clean copy, otherwise extraneous files
will be included in the release).

2. Run the ``create_deployment.bat`` file in the root of the cloned repository. This will run the ``create_deployment.ps1``
Powershell script. This script obtains all the required binary dependencies (including a standalone
version of Python) and places them in the correct place in the folder hierarchy, and then zips up the
entire folder, resulting in a file in the root of the cloned repository called ``pepys-import_HASH.zip``,
where ``HASH`` is the git commit hash that the release was created from.

3. Upload the resulting zip file to the Github Releases page.