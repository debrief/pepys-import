import os
import shutil
import sys
from stat import S_IREAD

import smbclient
import smbclient.path
import smbclient.shutil
from smbprotocol.exceptions import SMBAuthenticationError, SMBResponseException

from config import ARCHIVE_ON_SMB, ARCHIVE_PASSWORD, ARCHIVE_USER

SMB_ERROR_MESSAGE = (
    "Error connecting to archive location on Windows shared folder (SMB share). "
    + "Check config file details are correct and server is accessible."
)


auth = {"username": ARCHIVE_USER, "password": ARCHIVE_PASSWORD}


def exists(path):
    if ARCHIVE_ON_SMB:
        try:
            return smbclient.path.exists(path, **auth)
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        return os.path.exists(path)


def isdir(path):
    if ARCHIVE_ON_SMB:
        try:
            return smbclient.path.isdir(path, **auth)
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        return os.path.isdir(path)


def makedirs(path):
    if ARCHIVE_ON_SMB:
        try:
            return smbclient.makedirs(path, **auth)
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        return os.makedirs(path)


def move(from_path, to_path):
    if ARCHIVE_ON_SMB:
        try:
            # No move function in smbclient, so copy then delete original copy
            smbclient.shutil.copy(from_path, to_path, **auth)
            os.remove(from_path)
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        shutil.move(from_path, to_path)


def set_read_only(path):
    if ARCHIVE_ON_SMB:
        try:
            smbclient.shutil._set_file_basic_info(
                path, follow_symlinks=False, read_only=True, **auth
            )
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        os.chmod(path, S_IREAD)


def open_file(*args, **kwargs):
    if ARCHIVE_ON_SMB:
        try:
            return smbclient.open_file(*args, **kwargs, **auth)
        except (SMBAuthenticationError, SMBResponseException, ValueError):
            print(SMB_ERROR_MESSAGE)
            sys.exit()
    else:
        return open(*args, **kwargs)
