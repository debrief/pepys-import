import os
import shutil
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

from pepys_admin import admin_cli as cli
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
SAMPLE_DATA_PATH = os.path.join(FILE_PATH, "sample_data")
CSV_PATH = os.path.join(SAMPLE_DATA_PATH, "csv_files")
DATA_PATH = os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data")
MODULE_PATH = os.path.abspath(cli.__file__)


class AdminCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.admin_shell = cli.AdminShell(self.store)

    @patch("pepys_admin.admin_cli.iterfzf", return_value="rep_test1.rep")
    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_export(self, patched_iterfzf, patched_input):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "'rep_test1.rep' is going to be exported." in output
        assert "Datafile successfully exported to exported_rep_test1_rep.rep." in output

        file_path = os.path.join(CURRENT_DIR, "exported_rep_test1_rep.rep")
        assert os.path.exists(file_path) is True
        with open(file_path, "r") as file:
            data = file.read().splitlines()
        assert len(data) == 22  # 8 States, 7 Contacts, 7 Comments

    @patch("pepys_admin.admin_cli.iterfzf", return_value="NOT_EXISTING_FILE.rep")
    def test_do_export_invalid_datafile_name(self, patched_iterfzf):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "You haven't selected a valid option!" in output

    @patch("pepys_admin.admin_cli.iterfzf")
    @patch("pepys_admin.admin_cli.input")
    def test_do_export_other_options(self, patched_input, patched_iterfzf):
        patched_iterfzf.side_effect = ["rep_test1.rep", "rep_test1.rep"]
        patched_input.side_effect = ["n", "RANDOM-INPUT"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "You selected not to export!" in output
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "Please enter a valid input." in output

    def test_do_export_empty_database(self):
        # Create an empty database
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        new_data_store.initialise()
        new_shell = cli.AdminShell(new_data_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            new_shell.do_export()
        output = temp_output.getvalue()
        assert "There is no datafile found in the database!" in output

    @patch("pepys_admin.admin_cli.input")
    def test_do_export_all(self, patched_input):
        patched_input.side_effect = ["Y", "export_test"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Datafiles are going to be exported to 'export_test' folder" in output
        assert "All datafiles are successfully exported!" in output

        folder_path = os.path.join(CURRENT_DIR, "export_test")
        assert os.path.exists(folder_path) is True

        shutil.rmtree(folder_path)

    @patch("pepys_admin.admin_cli.input")
    def test_do_export_all_to_existing_folder(self, patched_input):
        patched_input.side_effect = ["Y", SAMPLE_DATA_PATH, "export_test"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert f"{SAMPLE_DATA_PATH} already exists." in output
        assert "Datafiles are going to be exported to 'export_test' folder" in output
        assert "All datafiles are successfully exported!" in output

        folder_path = os.path.join(CURRENT_DIR, "export_test")
        assert os.path.exists(folder_path) is True

        shutil.rmtree(folder_path)

    @patch("pepys_admin.admin_cli.input")
    def test_do_export_all_to_default_folder(self, patched_input):
        patched_input.side_effect = ["Y", None]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Datafiles are going to be exported to 'exported_datafiles_" in output
        assert "All datafiles are successfully exported!" in output

        folders = [
            folder for folder in os.listdir(CURRENT_DIR) if folder.startswith("exported_datafiles")
        ]
        for folder in folders:
            shutil.rmtree(folder)

    @patch("pepys_admin.admin_cli.input")
    def test_do_export_all_other_options(self, patched_input):
        patched_input.side_effect = ["n", "RANDOM-INPUT"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "You selected not to export!" in output
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Please enter a valid input." in output

    @patch("pepys_admin.admin_cli.input", return_value="Y")
    def test_do_export_all_empty_database(self, patched_input):
        # Create an empty database
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        new_data_store.initialise()
        new_shell = cli.AdminShell(new_data_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            new_shell.do_export_all()
        output = temp_output.getvalue()
        assert "There is no datafile found in the database!" in output

    @patch("cmd.input", return_value="0")
    def test_do_initialise(self, patched_input):
        initialise_shell = cli.InitialiseShell(self.store, None, None)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_initialise()
        output = temp_output.getvalue()
        # Assert that Admin Shell redirects to the initialise menu
        assert initialise_shell.intro in output

    def test_do_status(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_status()
        output = temp_output.getvalue()

        states_text = "| States       |              738 |"
        contacts_text = "| Contacts     |               15 |"
        comments_text = "| Comments     |                7 |"
        datafiles_text = "| Datafiles    |                7 |"
        assert states_text in output
        assert contacts_text in output
        assert comments_text in output
        assert datafiles_text in output

    def test_do_exit(self):
        temp_output = StringIO()
        with pytest.raises(SystemExit), redirect_stdout(temp_output):
            self.admin_shell.do_exit()
        output = temp_output.getvalue()
        assert "Thank you for using Pepys Admin" in output

    def test_default(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    def test_postcmd(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.admin_shell.intro in output


class InitialiseShellTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.admin_shell = cli.AdminShell(self.store, csv_path=CSV_PATH)
        self.initialise_shell = cli.InitialiseShell(self.store, self.admin_shell, CSV_PATH)

    def test_do_clear_db_contents(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
            self.initialise_shell.do_import_metadata()
            self.initialise_shell.do_import_sample_measurements()
            # Clear imported default entities
            self.initialise_shell.do_clear_db_contents()
        output = temp_output.getvalue()
        assert "Cleared database contents" in output

    def test_do_clear_db_schema(self):
        assert self.store.is_schema_created() is True

        self.initialise_shell.do_clear_db_schema()
        assert self.store.is_schema_created() is False

    def test_do_create_pepys_schema(self):
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        assert new_data_store.is_schema_created() is False

        new_shell = cli.InitialiseShell(new_data_store, None, None)
        new_shell.do_create_pepys_schema()
        assert new_data_store.is_schema_created() is True

    def test_do_import_reference_data(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
        output = temp_output.getvalue()
        assert "Reference data imported" in output

    def test_do_import_metadata(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
            self.initialise_shell.do_import_metadata()
        output = temp_output.getvalue()
        assert "Reference data imported" in output
        assert "Metadata imported" in output

    def test_do_import_sample_measurements(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
            self.initialise_shell.do_import_metadata()
            self.initialise_shell.do_import_sample_measurements()
        output = temp_output.getvalue()
        assert "Reference data imported" in output
        assert "Metadata imported" in output
        assert "Sample measurements imported" in output

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    def test_default(self):
        # Only cancel command (0) returns True, others return None
        result = self.initialise_shell.default("0")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    def test_postcmd(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.initialise_shell.intro in output


class NotInitialisedDBTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.admin_shell = cli.AdminShell(self.store)
        self.initialise_shell = cli.InitialiseShell(
            self.store, self.admin_shell, self.admin_shell.csv_path
        )

    def test_not_initialised_db(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_status()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_clear_db_contents()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_clear_db_schema()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_metadata()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_sample_measurements()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output


if __name__ == "__main__":
    unittest.main()
