import os
import shutil
from stat import S_IREAD

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


def move(from_path, to_path):
    if ARCHIVE_ON_SMB:
        # No move function in smbclient, so copy then delete original copy
        smbclient.shutil.copy(from_path, to_path, **auth)
        os.remove(from_path)
    else:
        shutil.move(from_path, to_path)


def set_read_only(path):
    if ARCHIVE_ON_SMB:
        smbclient.shutil._set_file_basic_info(path, follow_symlinks=False, read_only=True, **auth)
    else:
        os.chmod(path, S_IREAD)


def open_file(*args, **kwargs):
    if ARCHIVE_ON_SMB:
        return smbclient.open_file(*args, **kwargs, **auth)
    else:
        return open(*args, **kwargs)
