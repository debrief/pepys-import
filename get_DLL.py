import sys

for path in sys.path:
    if "DLL" in path:
        print(path + "\\_sqlite3.pyd")
        break
