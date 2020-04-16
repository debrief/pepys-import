import os


def running_on_travis():
    if os.getenv("travis"):
        return True
    else:
        return False
