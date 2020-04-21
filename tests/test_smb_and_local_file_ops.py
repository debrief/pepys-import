import stat
from unittest.mock import Mock, patch

import pytest

import pepys_import.file.smb_and_local_file_operations as smblocal

AUTH_DETAILS = {"username": "archive_username", "password": "archive_password"}

#
# Fixtures
#
# (Used to provide patches for the functions with less boilerplate)


@pytest.fixture()
def archive_on_smb_true():
    with patch("pepys_import.file.smb_and_local_file_operations.ARCHIVE_ON_SMB", True):
        yield


@pytest.fixture()
def archive_on_smb_false():
    with patch("pepys_import.file.smb_and_local_file_operations.ARCHIVE_ON_SMB", False):
        yield


@pytest.fixture()
def archive_user_password():
    with patch(
        "pepys_import.file.smb_and_local_file_operations.auth", AUTH_DETAILS,
    ):
        yield


@pytest.fixture()
def smbclient():
    with patch("pepys_import.file.smb_and_local_file_operations.smbclient", Mock()) as p:
        yield p


@pytest.fixture()
def os():
    with patch("pepys_import.file.smb_and_local_file_operations.os", Mock()) as p:
        yield p


@pytest.fixture()
def shutil():
    with patch("pepys_import.file.smb_and_local_file_operations.shutil", Mock()) as p:
        yield p


@pytest.fixture()
def patched_open():
    with patch("pepys_import.file.smb_and_local_file_operations.open", Mock()) as p:
        yield p


#
# Tests
#


def test_exists_smb(archive_on_smb_true, archive_user_password, smbclient):
    smblocal.exists("blah")

    smbclient.path.exists.assert_called_once_with("blah", **AUTH_DETAILS)


def test_exists_local(archive_on_smb_false, os):
    smblocal.exists("blah")

    os.path.exists.assert_called_once_with("blah")


def test_isdir_smb(archive_on_smb_true, archive_user_password, smbclient):
    smblocal.isdir("blah")

    smbclient.path.isdir.assert_called_once_with("blah", **AUTH_DETAILS)


def test_isdir_local(archive_on_smb_false, os):
    smblocal.isdir("blah")

    os.path.isdir.assert_called_once_with("blah")


def test_makedirs_smb(archive_on_smb_true, archive_user_password, smbclient):
    smblocal.makedirs("\\\\SERVER\\share\\test\\path")

    smbclient.makedirs.assert_called_once_with("\\\\SERVER\\share\\test\\path", **AUTH_DETAILS)


def test_makedirs_local(archive_on_smb_false, os):
    smblocal.makedirs("test/path")

    os.makedirs.assert_called_once_with("test/path")


def test_move_smb(archive_on_smb_true, archive_user_password, smbclient, os):
    smblocal.move("from/path/file.txt", "to/path/file.txt")

    smbclient.shutil.copy.assert_called_once_with(
        "from/path/file.txt", "to/path/file.txt", **AUTH_DETAILS
    )
    os.remove.assert_called_once_with("from/path/file.txt")


def test_move_local(archive_on_smb_false, shutil):
    smblocal.move("from/path/file.txt", "to/path/file.txt")

    shutil.move.assert_called_once_with("from/path/file.txt", "to/path/file.txt")


def test_set_read_only_smb(archive_on_smb_true, archive_user_password, smbclient):
    smblocal.set_read_only("path/to/file.txt")

    smbclient.shutil._set_file_basic_info.assert_called_once_with(
        "path/to/file.txt", follow_symlinks=False, read_only=True, **AUTH_DETAILS
    )


def test_set_read_only_local(archive_on_smb_false, os):
    smblocal.set_read_only("path/to/file.txt")

    os.chmod.assert_called_once_with("path/to/file.txt", stat.S_IREAD)


def test_open_file_smb(archive_on_smb_true, archive_user_password, smbclient):
    f = smblocal.open_file("path/to/file.txt", "w")
    f.close()

    smbclient.open_file.assert_called_once_with("path/to/file.txt", "w", **AUTH_DETAILS)


def test_open_file_local(archive_on_smb_false, patched_open):
    f = smblocal.open_file("path/to/file.txt", "w")
    f.close()

    patched_open.assert_called_once_with("path/to/file.txt", "w")
