import os

import smbclient
import smbclient.path
import smbclient.shutil

from config import ARCHIVE_ON_SMB, ARCHIVE_PASSWORD, ARCHIVE_USER

auth = {"username": ARCHIVE_USER, "password": ARCHIVE_PASSWORD}


def exists(path):
    if ARCHIVE_ON_SMB:
        return smbclient.path.exists(path, **auth)
    else:
        return os.path.exists(path)


def isdir(path):
    if ARCHIVE_ON_SMB:
        return smbclient.path.isdir(path, **auth)
    else:
        return os.path.isdir(path)


def makedirs(path):
    if ARCHIVE_ON_SMB:
        return smbclient.makedirs(path, **auth)
    else:
        return os.makedirs(path)
