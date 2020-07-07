import os
import shutil
import sys
from contextlib import contextmanager
from stat import S_IREAD

import smbclient
import smbclient.path
import smbclient.shutil
from smbprotocol.exceptions import SMBAuthenticationError, SMBResponseException

from config import ARCHIVE_ON_SMB, ARCHIVE_PASSWORD, ARCHIVE_USER


@contextmanager
def handle_smb_errors():
    try:
        yield
    except (SMBAuthenticationError, SMBResponseException, ValueError) as e:
        print(e)
        print(
            "Error connecting to archive location on Windows shared folder (SMB share). "
            + "Check config file details are correct and server is accessible. See full error above."
        )
        sys.exit()


auth = {"username": ARCHIVE_USER, "password": ARCHIVE_PASSWORD}


def exists(path):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            smbclient.path.exists(path, **auth)
    else:
        return os.path.exists(path)


def isdir(path):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            return smbclient.path.isdir(path, **auth)
    else:
        return os.path.isdir(path)


def makedirs(path):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            return smbclient.makedirs(path, **auth)
    else:
        return os.makedirs(path)


def move(from_path, to_path):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            # No move function in smbclient, so copy then delete original copy
            smbclient.shutil.copy(from_path, to_path, **auth)
            os.remove(from_path)
    else:
        shutil.move(from_path, to_path)


def set_read_only(path):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            smbclient.shutil._set_file_basic_info(
                path, follow_symlinks=False, read_only=True, **auth
            )
    else:
        os.chmod(path, S_IREAD)


def open_file(*args, **kwargs):
    if ARCHIVE_ON_SMB:
        with handle_smb_errors():
            return smbclient.open_file(*args, **kwargs, **auth)
    else:
        return open(*args, **kwargs)
