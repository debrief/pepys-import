import os
import platform


def running_on_ci():
    if os.getenv("GITHUB_ACTIONS") and platform.system() != "Windows":
        return True
    else:
        return False
