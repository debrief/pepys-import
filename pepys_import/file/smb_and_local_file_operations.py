import os

import smbclient
import smbclient.path
import smbclient.shutil

from config import ARCHIVE_ON_SMB, ARCHIVE_PASSWORD, ARCHIVE_PATH, ARCHIVE_USER

auth = {"username": ARCHIVE_USER, "password": ARCHIVE_PASSWORD}


def create_archive_path_if_not_exists():
    if ARCHIVE_ON_SMB:
        print(ARCHIVE_PATH)
        print(auth)
        if not smbclient.path.exists(ARCHIVE_PATH, **auth):
            smbclient.makedirs(ARCHIVE_PATH, **auth)
    else:
        if not os.path.exists(ARCHIVE_PATH):
            os.makedirs(ARCHIVE_PATH)


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
