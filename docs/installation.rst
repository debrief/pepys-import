.. highlight:: shell

============
Installation
============

Deployable releases of pepys-import are available on the `Releases
<https://github.com/debrief/pepys-import/releases>`_ page. Download the latest release and follow the
instructions below to install:

1. Before code can be run from inside the release, MS-Windows must be instructed that it's safe to
do that for this file. Right-click on the `zip-file` and select ``Properties``. Once the dialog opens,
tick the ``Unblock`` checkbox from the security section at the bottom. Then click ``OK``.

2. Extract the contents of the downloaded zip file into a folder of your choice (note, this can be
anywhere, including on a shared network drive). This zip file contains everything that is needed
to run pepys-import - including a standalone installation of Python, all of the Python dependencies,
various required DLLs and the pepys-import code itself.

3. Once for each user who will use pepys-import, run ``create_shortcuts.bat`` in the ``bin`` directory.
This will create shortcuts to the relevant pepys-import batch files (from the ``bin`` directory) and copy
them to the user's *Send To* folder, and their *Start Menu*.