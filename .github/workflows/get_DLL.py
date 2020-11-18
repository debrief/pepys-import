# This script is called by the setup_windows.ps1 Powershell script
# and finds the path to the _sqlite3.pyd file, which needs to be copied
# to a separate folder as part of the setup
#
# We can't hardcode the path to it because it will change based on the exact
# version of Python (including point releases)
import sys

for path in sys.path:
    if "DLL" in path:
        print(path + "\\_sqlite3.pyd")
        break
