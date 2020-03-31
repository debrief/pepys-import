=====
Usage
=====

The main way to use pepys-import is through the `import` command-line module. This can be run
in two ways:

 - **Send To:** On a Windows deployment, the import command is available in the *Send To* menu. Right-click on a folder or 
   file you want to import, and choose either :code:`Pepys Import` to import using the default settings
   or :code:`Pepys Import (no archive)` to import without archiving the imported files.

 - **Manually:** Run :code:`python -m pepys_import.import <options>` on the command-line, ensuring that the `python`
   executable on your PATH is the one for which pepys-import has been installed.

Command-line options
--------------------

.. code-block:: none

   usage: import.py [-h] [--path PATH] [--archive]

   optional arguments:
   -h, --help   show this help message and exit
   --path PATH  The path to import data from (The default value is the
             directory of the script)
   --archive    Instruction to archive (move) imported files to designated
                archive folder
