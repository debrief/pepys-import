import os

from IPython import get_ipython


def setup():
    get_ipython().run_line_magic("reload_ext", "notebook_xterm")
    if os.path.basename(os.getcwd()) == "docs":
        os.chdir("..")
    try:
        del os.environ["PEPYS_CONFIG_FILE"]
    except KeyError:
        pass
    print("Set up complete")
