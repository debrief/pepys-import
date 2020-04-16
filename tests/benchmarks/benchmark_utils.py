import os


def running_on_travis():
    if os.getenv("travis") == "true":
        return True
    else:
        return False
