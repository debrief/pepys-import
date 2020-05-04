.. highlight:: shell

====================
Installation/Upgrade
====================

Deployable releases of pepys-import are available on the `Releases
<https://github.com/debrief/pepys-import/releases>`_ page. Download the latest release and follow the
instructions below to install. The same instructions can be used to upgrade a previously-installed version.

1. Before code can be run from inside the release, MS-Windows must be instructed that it's safe to
do that for this file. Right-click on the `zip-file` and select ``Properties``. Once the dialog opens,
tick the ``Unblock`` checkbox from the security section at the bottom. Then click ``OK``.

2. If there is a previous Pepys install present, then delete the main Pepys install folder (the
folder where you extracted the release zip file when you installed Pepys originally). 

3. Extract the contents of the downloaded zip file into a folder of your choice (note, this can be
anywhere, including on a shared network drive). If you're upgrading, then this folder should be the
same folder that you used for the previous installation. This zip file contains everything that is
needed to run pepys-import - including a standalone installation of Python, all of the Python
dependencies, various required DLLs and the pepys-import code itself.

4. Once for each user who will use pepys-import (including the user who is running this install),
run ``install_pepys.bat`` in the ``bin`` directory. This will create shortcuts to the relevant
pepys-import batch files in the user's *Send To* and *Start Menu* folders, and add the Pepys
:code:`bin` directory to the user's PATH. If you're upgrading, then this will just overwrite the existing
shortcuts - it won't create duplicates.

5. Create a Pepys configuration file in any location you choose, and set the
:code:`PEPYS_CONFIG_FILE` environment variable to the full path to the configuration file. An
example configuration file is provided as :code:`default_config.ini` in the Pepys installation
folder. Full details on the configuration file syntax are available in the :doc:`configuration`
documentation. The default configuration file specifies a connection to a SQLite database: for
deployment you will probably want to change this to connect to a Postgres server. 

6. Open *Pepys Admin* from the Start Menu, and choose option :code:`5` for the _Migrate_ option. This will
update or create the Pepys database schema.