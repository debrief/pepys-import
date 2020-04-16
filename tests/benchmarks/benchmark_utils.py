import os


def running_on_travis():
    if os.getenv("TRAVIS"):
        return True
    else:
        return False
