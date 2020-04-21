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


def isdir(dir):
    if ARCHIVE_ON_SMB:
        return smbclient.path.isdir(dir)
    else:
        return os.path.isdir(dir)


def makedirs(path):
    if ARCHIVE_ON_SMB:
        return smbclient.makedirs(path)
    else:
        return os.makedirs(path)
