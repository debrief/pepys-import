import os
import shutil
import sqlite3
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO
from sqlite3 import OperationalError
from unittest.mock import ANY, patch

import pg8000
import pytest
from testing.postgresql import Postgresql

from paths import MIGRATIONS_DIRECTORY
from pepys_admin.admin_cli import AdminShell
from pepys_admin.cli import run_shell
from pepys_admin.export_cli import ExportByPlatformNameShell, ExportShell
from pepys_admin.initialise_cli import InitialiseShell
from pepys_admin.snapshot_cli import SnapshotShell
from pepys_admin.utils import database_at_latest_revision
from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.data_store_utils import is_schema_created
from pepys_import.utils.sqlite_utils import load_spatialite
from pepys_import.utils.text_formatting_utils import formatted_text_to_str
from tests.utils import move_and_overwrite, side_effect

FILE_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
SAMPLE_DATA_PATH = os.path.join(FILE_PATH, "sample_data")
CSV_PATH = os.path.join(SAMPLE_DATA_PATH, "csv_files")
DATA_PATH = os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data")
CONFIG_FILE_PATH = os.path.join(
    FILE_PATH, "config_file_tests", "example_config", "config_for_do_migrate.ini"
)


class AdminCLITestCase(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def setUp(self, patched_prompt) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.admin_shell = AdminShell(self.store)

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input", return_value=".")
    def test_do_initialise(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        initialise_shell = InitialiseShell(self.store, None, None)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_initialise()
        output = temp_output.getvalue()
        # Assert that Admin Shell redirects to the initialise menu
        assert initialise_shell.choices in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input", return_value=".")
    def test_do_export(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        shell = ExportShell(self.store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_export()
        output = temp_output.getvalue()
        # Assert that Admin Shell redirects to the initialise menu
        assert shell.choices in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input", return_value=".")
    def test_do_snapshot(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        shell = SnapshotShell(self.store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_snapshot()
        output = temp_output.getvalue()
        # Assert that Admin Shell redirects to the initialise menu
        assert shell.choices in output

    @patch("pepys_admin.admin_cli.custom_print_formatted_text")
    def test_do_status(self, patched_print):
        # Use normal print() to capture table reports
        def side_effect(text):
            print(formatted_text_to_str(text))

        patched_print.side_effect = side_effect

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_status()
        output = temp_output.getvalue()

        states_text = "| States       |              738 |"
        contacts_text = "| Contacts     |              110 |"
        comments_text = "| Comments     |                7 |"
        sensors_text = "| Sensors      |               13 |"
        platforms_text = "| Platforms    |                6 |"
        datafiles_text = "| Datafiles    |                5 |"
        assert states_text in output
        assert contacts_text in output
        assert comments_text in output
        assert sensors_text in output
        assert platforms_text in output
        assert datafiles_text in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input", return_value=".")
    def test_do_view_data(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        view_data_shell = ViewDataShell(self.store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_view_data()
        output = temp_output.getvalue()
        # Assert that Admin Shell redirects to the view data menu
        assert view_data_shell.choices in output

    def test_do_exit(self):
        temp_output = StringIO()
        with pytest.raises(SystemExit), redirect_stdout(temp_output):
            self.admin_shell.do_exit()
        output = temp_output.getvalue()
        assert "Thank you for using Pepys Admin" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_default(self, patched_print):
        patched_print.side_effect = side_effect
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_postcmd(self, patched_print):
        patched_print.side_effect = side_effect
        # postcmd method should print the menu again if the user didn't select exit (".")
        # Select Export
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.admin_shell.choices in output
        # Select Initialise/Clear
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.postcmd(stop=None, line="2")
        output = temp_output.getvalue()
        assert self.admin_shell.choices in output
        # Select Status
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.postcmd(stop=None, line="3")
        output = temp_output.getvalue()
        assert self.admin_shell.choices in output
        # Select Export All
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.postcmd(stop=None, line="9")
        output = temp_output.getvalue()
        assert self.admin_shell.choices in output


class InitialiseShellTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.admin_shell = AdminShell(self.store, csv_path=CSV_PATH)
        self.initialise_shell = InitialiseShell(self.store, self.admin_shell, CSV_PATH)

    @patch("pepys_admin.initialise_cli.prompt", return_value="Y")
    def test_do_clear_db_contents(self, patched_input):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_import_reference_data()
            self.initialise_shell.do_import_metadata()
            # Clear imported default entities
            self.initialise_shell.do_clear_db_contents()
        output = temp_output.getvalue()
        assert "Cleared database contents" in output

    @patch("pepys_admin.initialise_cli.prompt", return_value="Y")
    def test_do_clear_db_schema(self, patched_input):
        assert is_schema_created(self.store.engine, self.store.db_type) is True

        self.initialise_shell.do_clear_db_schema()
        assert is_schema_created(self.store.engine, self.store.db_type) is False

    def test_do_create_pepys_schema(self):
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        assert is_schema_created(new_data_store.engine, new_data_store.db_type) is False

        new_shell = InitialiseShell(new_data_store, None, None)
        new_shell.do_create_pepys_schema()
        assert is_schema_created(new_data_store.engine, new_data_store.db_type) is True

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

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_default(self, patched_print):
        patched_print.side_effect = side_effect
        # Only cancel command (0) returns True, others return None
        result = self.initialise_shell.default(".")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_postcmd(self, patched_print):
        patched_print.side_effect = side_effect
        # postcmd method should print the menu again if the user didn't select cancel (".")
        # Select Clear database contents
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output
        # Select Clear database schema
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="2")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output
        # Select Create Pepys schema
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="3")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output
        # Select Import Reference data
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="4")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output
        # Select Import Metadata
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="5")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output
        # Select Import Sample Measurements
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.postcmd(stop=None, line="6")
        output = temp_output.getvalue()
        assert self.initialise_shell.choices in output


class InitialiseShellDefaultCSVLocTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.admin_shell = AdminShell(self.store)
        self.initialise_shell = InitialiseShell(self.store, self.admin_shell, None)

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


class NotInitialisedDBTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.admin_shell = AdminShell(self.store)
        self.export_shell = ExportShell(self.store)
        self.snapshot_shell = SnapshotShell(self.store)
        self.initialise_shell = InitialiseShell(
            self.store, self.admin_shell, self.admin_shell.csv_path
        )

    @patch("pepys_import.utils.data_store_utils.custom_print_formatted_text")
    def test_not_initialised_db(self, patched_print):
        patched_print.side_effect = side_effect
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.initialise_shell.do_clear_db_contents()
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
            self.export_shell.do_export_by_platform_name()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.admin_shell.do_view_data()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.snapshot_shell.do_export_reference_data()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.snapshot_shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Database tables are not found! (Hint: Did you initialise the DataStore?)" in output


class ExportShellTestCase(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def setUp(self, patched_prompt) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.export_shell = ExportShell(self.store)

    @patch("pepys_admin.export_cli.iterfzf", return_value="rep_test1.rep")
    @patch("pepys_admin.export_cli.ptk_prompt", side_effect=["Y", "."])
    def test_do_export(self, patched_iterfzf, patched_ptk_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export()
        output = temp_output.getvalue()
        assert "'rep_test1.rep' is going to be exported." in output

        file_path = os.path.join(".", "exported_rep_test1_rep.rep")
        assert f"Datafile successfully exported to {file_path}." in output

        assert os.path.exists(file_path) is True
        with open(file_path, "r") as file:
            data = file.read().splitlines()
        assert len(data) == 22  # 8 States, 7 Contacts, 7 Comments

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    @patch("pepys_admin.export_cli.iterfzf", return_value="NOT_EXISTING_FILE.rep")
    def test_do_export_invalid_datafile_name(self, patched_iterfzf, patched_print):
        patched_print.side_effect = side_effect
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export()
        output = temp_output.getvalue()
        assert "You haven't selected a valid option!" in output

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    @patch("pepys_admin.export_cli.iterfzf")
    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_other_options(self, patched_input, patched_iterfzf, patched_print):
        patched_print.side_effect = side_effect
        patched_iterfzf.side_effect = ["rep_test1.rep", "rep_test1.rep"]
        patched_input.side_effect = ["n", "RANDOM-INPUT"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export()
        output = temp_output.getvalue()
        assert "You selected not to export!" in output
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export()
        output = temp_output.getvalue()
        assert "Please enter a valid input." in output

    @patch("pepys_admin.export_cli.custom_print_formatted_text", side_effect=side_effect)
    def test_do_export_empty_database(self, patched_print):
        # Create an empty database
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        new_data_store.initialise()
        new_shell = ExportShell(new_data_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            new_shell.do_export()
        output = temp_output.getvalue()
        assert "There is no datafile found in the database!" in output

    @patch("pepys_admin.export_cli.iterfzf", return_value="SEARCH_PLATFORM")
    @patch("cmd.input", return_value="1")
    @patch("pepys_admin.export_cli.ptk_prompt", side_effect=["", "."])
    def test_do_export_by_platform_name(self, cmd_input, patched_iterfzf, patched_ptk_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_by_platform_name()
        output = temp_output.getvalue()

        file_path = os.path.join(".", "exported_SENSOR-1.rep")
        assert os.path.exists(file_path) is True

        assert f"Objects are going to be exported to '{file_path}'." in output
        assert f"Objects successfully exported to {file_path}" in output

        with open(file_path, "r") as file:
            data = file.read().splitlines()
        assert len(data) == 4  # 4 State objects

        os.remove(file_path)

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    @patch("pepys_admin.export_cli.iterfzf", return_value="NOT_EXISTING_PLATFORM")
    def test_do_export_by_platform_name_invalid_platform_name(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_by_platform_name()
        output = temp_output.getvalue()
        assert "You haven't selected a valid option!" in output

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    def test_do_export_by_platform_name_empty_database(self, patched_print):
        patched_print.side_effect = side_effect
        # Create an empty database
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        new_data_store.initialise()
        new_shell = ExportShell(new_data_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            new_shell.do_export_by_platform_name()
        output = temp_output.getvalue()
        assert "There is no platform found in the database!" in output

    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_all(self, patched_input):
        patched_input.side_effect = ["Y", "export_test"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Datafiles are going to be exported to 'export_test' folder" in output
        assert "All datafiles are successfully exported!" in output

        folder_path = os.path.join(CURRENT_DIR, "export_test")
        assert os.path.exists(folder_path) is True

        shutil.rmtree(folder_path)

    @patch("pepys_admin.export_cli.custom_print_formatted_text", side_effect=side_effect)
    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_all_to_existing_folder(self, patched_input, patched_print):
        patched_input.side_effect = ["Y", SAMPLE_DATA_PATH, "export_test"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert f"{SAMPLE_DATA_PATH} already exists." in output
        assert "Datafiles are going to be exported to 'export_test' folder" in output
        assert "All datafiles are successfully exported!" in output

        folder_path = os.path.join(CURRENT_DIR, "export_test")
        assert os.path.exists(folder_path) is True

        shutil.rmtree(folder_path)

    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_all_to_default_folder(self, patched_input):
        patched_input.side_effect = ["Y", None]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Datafiles are going to be exported to 'exported_datafiles_" in output
        assert "All datafiles are successfully exported!" in output

        folders = [
            folder for folder in os.listdir(CURRENT_DIR) if folder.startswith("exported_datafiles")
        ]
        for folder in folders:
            shutil.rmtree(folder)

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_all_other_options(self, patched_input, patched_print):
        patched_print.side_effect = side_effect
        patched_input.side_effect = ["n", "RANDOM-INPUT"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert "You selected not to export!" in output
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_export_all()
        output = temp_output.getvalue()
        assert "Please enter a valid input." in output

    @patch("pepys_admin.export_cli.custom_print_formatted_text", side_effect=side_effect)
    @patch("pepys_admin.export_cli.ptk_prompt")
    def test_do_export_all_empty_database(self, patched_input, patched_print):
        patched_input.side_effect = ["Y", "export_test"]
        # Create an empty database
        new_data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        new_data_store.initialise()
        new_shell = ExportShell(new_data_store)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            new_shell.do_export_all()
        output = temp_output.getvalue()
        assert "There is no datafile found in the database!" in output

        output_path = os.path.join(CURRENT_DIR, "export_test")
        shutil.rmtree(output_path)

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_default(self, patched_print):
        patched_print.side_effect = side_effect
        # Only cancel command (0) returns True, others return None
        result = self.export_shell.default(".")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_postcmd(self, patched_print):
        patched_print.side_effect = side_effect
        # postcmd method should print the menu again if the user didn't select cancel (".")
        # Select Export by name
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.export_shell.choices in output
        # Select Export by platform and sensor
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.export_shell.postcmd(stop=None, line="2")
        output = temp_output.getvalue()
        assert self.export_shell.choices in output


class ExportByPlatformNameShellTestCase(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def setUp(self, patched_prompt) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        Sensor = self.store.db_classes.Sensor
        with self.store.session_scope():
            platform_id = self.store.search_platform("SEARCH_PLATFORM", "UK", "123").platform_id
            sensors = self.store.session.query(Sensor).filter(Sensor.host == platform_id).all()
            sensors_dict = {s.name: s.sensor_id for s in sensors}
            self.objects = self.store.find_related_datafile_objects(platform_id, sensors_dict)
        # Create a dynamic menu for the found datafile objects
        self.text = ""
        self.options = [
            ".",
        ]
        for index, obj in enumerate(self.objects, 1):
            self.text += f"({index}) {obj['name']} {obj['filename']} {obj['min']}-{obj['max']}\n"
            self.options.append(str(index))
        self.text += "(.) Cancel\n"
        # Initialise a new menu
        self.shell = ExportByPlatformNameShell(
            self.store, "--- Menu ---\n", self.text, self.options, self.objects
        )

    @patch("pepys_admin.export_cli.ptk_prompt", side_effect=["export_test", "."])
    def test_do_export(self, patched_ptk_prompt):
        print(self.objects)
        search_platform_obj = [item for item in self.objects if item["name"] == "SENSOR-1"][0]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export(search_platform_obj)
        output = temp_output.getvalue()

        file_path = os.path.join(".", "export_test.rep")
        assert os.path.exists(file_path) is True

        assert f"Objects are going to be exported to '{file_path}'." in output
        assert f"Objects successfully exported to {file_path}" in output

        with open(file_path, "r") as file:
            data = file.read().splitlines()
        assert len(data) == 4  # 4 State objects
        assert (
            "100112 115800.000\tSEARCH_PLATFORM\tAA\t60 28 56.02 N\t000 35 59.68 E\t179.84\t8.00\t"
            "0.0" in data
        )
        assert (
            "100112 121400.000\tSEARCH_PLATFORM\tAA\t60 28 8.02 N\t000 35 59.95 E\t179.84\t8.00\t"
            "0.0" in data
        )

        os.remove(file_path)

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    @patch("pepys_admin.export_cli.custom_print_formatted_text")
    def test_default(self, patched_print):
        patched_print.side_effect = side_effect
        result = self.shell.default(".")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_postcmd(self, patched_print):
        patched_print.side_effect = side_effect
        # postcmd method should print the menu again if stop parameter is false
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.postcmd(stop=False, line="123456789")
        output = temp_output.getvalue()
        assert self.shell.choices in output


class AdminCLIMissingDBColumnTestCaseSQLite(unittest.TestCase):
    def setUp(self):
        ds = DataStore("", "", "", 0, "cli_import_test.db", db_type="sqlite")
        ds.initialise()

    def tearDown(self):
        os.remove("cli_import_test.db")

    @patch("pepys_import.utils.error_handling.custom_print_formatted_text")
    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("pepys_admin.view_data_cli.iterfzf", return_value="States")
    @patch("cmd.input")
    def test_missing_db_column_sqlite(
        self, patched_input, patched_iterfzf, patched_print, patched_print2
    ):
        patched_print.side_effect = side_effect
        patched_print2.side_effect = side_effect
        patched_input.side_effect = ["6", "1"]
        conn = sqlite3.connect("cli_import_test.db")
        load_spatialite(conn, None)

        # We want to DROP a column from the States table, but SQLite doesn't support this
        # so we drop the table and create a new table instead
        conn.execute("DROP TABLE States")

        # SQL to create a States table without a time column
        create_sql = """CREATE TABLE States (
        state_id INTEGER NOT NULL,
        sensor_id INTEGER NOT NULL,
        elevation REAL,
        heading REAL,
        course REAL,
        speed REAL,
        source_id INTEGER NOT NULL,
        privacy_id INTEGER,
        created_date DATETIME, "location" POINT,
        PRIMARY KEY (state_id)
        )"""

        conn.execute(create_sql)
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            data_store = DataStore("", "", "", 0, "cli_import_test.db", db_type="sqlite")
            run_shell(data_store=data_store, path=".")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output

    @patch("pepys_import.utils.error_handling.custom_print_formatted_text")
    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input")
    def test_missing_db_column_sqlite_2(self, patched_input, patched_print, patched_print2):
        patched_print.side_effect = side_effect
        patched_print2.side_effect = side_effect
        patched_input.side_effect = ["2", "."]
        conn = sqlite3.connect("cli_import_test.db")
        load_spatialite(conn, None)

        # We want to DROP a column from the States table, but SQLite doesn't support this
        # so we drop the table and create a new table instead
        conn.execute("DROP TABLE States")

        # SQL to create a States table without a heading column
        create_sql = """CREATE TABLE States (
        state_id INTEGER NOT NULL,
        time TIMESTAMP NOT NULL,
        sensor_id INTEGER NOT NULL,
        elevation REAL,
        course REAL,
        speed REAL,
        source_id INTEGER NOT NULL,
        privacy_id INTEGER,
        created_date DATETIME, "location" POINT,
        PRIMARY KEY (state_id)
        )"""

        conn.execute(create_sql)
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            data_store = DataStore("", "", "", 0, "cli_import_test.db", db_type="sqlite")
            run_shell(data_store=data_store, path=".")
        output = temp_output.getvalue()

        assert "ERROR: Table summaries couldn't be printed." in output


@pytest.mark.postgres
class TestAdminCLIWithMissingDBFieldPostgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None
        self.store = None
        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            raise Exception("Testing Postgres server could not be started/accessed")
        try:
            self.store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            self.store.initialise()
        except OperationalError:
            raise Exception("Creating database schema in testing Postgres database failed")

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    @patch("pepys_import.utils.error_handling.custom_print_formatted_text")
    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("pepys_admin.view_data_cli.iterfzf", return_value="States")
    @patch("cmd.input")
    def test_missing_db_column_postgres(
        self, patched_input, patched_iterfzf, patched_print, patched_print2
    ):
        patched_print.side_effect = side_effect
        patched_print2.side_effect = side_effect
        patched_input.side_effect = ["6", "1"]
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to drop heading column
        cursor.execute('ALTER TABLE pepys."States" DROP COLUMN time CASCADE;')

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            data_store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            run_shell(data_store=data_store, path=".")
        output = temp_output.getvalue()

        assert "ERROR: SQL error when communicating with database" in output

    @patch("pepys_import.utils.error_handling.custom_print_formatted_text")
    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    @patch("cmd.input")
    def test_missing_db_column_postgres_2(self, patched_input, patched_print, patched_print2):
        patched_print.side_effect = side_effect
        patched_print2.side_effect = side_effect
        patched_input.side_effect = ["2", "."]
        conn = pg8000.connect(user="postgres", password="postgres", database="test", port=55527)
        cursor = conn.cursor()
        # Alter table to drop heading column
        cursor.execute('ALTER TABLE pepys."States" DROP COLUMN time CASCADE;')

        conn.commit()
        conn.close()

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            data_store = DataStore(
                db_name="test",
                db_host="localhost",
                db_username="postgres",
                db_password="postgres",
                db_port=55527,
                db_type="postgres",
            )
            run_shell(data_store=data_store, path=".")
        output = temp_output.getvalue()

        assert "ERROR: Table summaries couldn't be printed." in output


@pytest.mark.postgres
class SnapshotPostgresTestCase(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def setUp(self, patched_prompt) -> None:
        self.postgres = Postgresql(
            database="test",
            host="localhost",
            user="postgres",
            password="postgres",
            port=55527,
        )
        self.store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )
        self.store.initialise()
        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files/other_data"), self.store, False
        )
        processor.process(os.path.join(DATA_PATH), self.store, False)

        with self.store.session_scope():
            self.store.populate_reference()
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "test").change_id
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter(self.store.db_classes.Privacy.name == "Public")
                .first()
            )
            platform_id = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.privacy_id == privacy.privacy_id)
                .first()
                .platform_id
            )
            privacy_2 = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter(self.store.db_classes.Privacy.name == "Public Sensitive")
                .first()
            )
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-TEST", change_id)
            nationality = self.store.add_to_nationalities("UK", change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", change_id).name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy.name,
                change_id=change_id,
            )
            platform.get_sensor(
                self.store,
                "SENSOR-TEST",
                sensor_type=sensor_type.name,
                privacy=privacy_2.name,
                change_id=change_id,
            )
            self.store.add_to_synonyms("Platforms", "test", entity=platform_id, change_id=change_id)

        self.shell = SnapshotShell(self.store)

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    def test_do_export_reference_data_postgres(self, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data()
        output = temp_output.getvalue()
        assert "Reference tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM DatafileTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Replay" in names
        assert "GPX" in names
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public", "Public Sensitive"])
    def test_do_export_reference_data_and_metadata_postgres(self, patched_iterfzf, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "SENSOR-1" in names
        assert "New_SSK_FREQ" in names
        assert "E-Trac" in names
        assert "SENSOR-TEST" in names

        results = connection.execute("SELECT * FROM Synonyms;")
        results = results.fetchall()
        table_dict = {row[1]: row[3] for row in results}
        assert "Platforms" in table_dict.keys()
        assert "test" in table_dict.values()
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public"])
    def test_do_export_reference_data_and_metadata_public(self, patched_iterfzf, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "SENSOR-1" in names
        assert "New_SSK_FREQ" in names
        assert "E-Trac" in names
        assert "SENSOR-TEST" not in names

        results = connection.execute("SELECT * FROM Synonyms;")
        results = results.fetchall()
        table_dict = {row[1]: row[3] for row in results}
        assert "Platforms" in table_dict.keys()
        assert "test" in table_dict.values()
        assert "Sensors" not in table_dict.keys()
        assert "test-2" not in table_dict.values()
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public Sensitive"])
    def test_do_export_reference_data_and_metadata_public_sensitive(
        self, patched_iterfzf, patched_input
    ):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        # Even though there are Sensor objects with Public Sensitive level, their Platform objects
        # have different privacy values. Therefore, none of platforms and sensors are exported.
        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        assert len(results) == 0
        connection.close()

        remove_file_if_exists("test.db")


class SnapshotShellMergingTestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists("slave.db"):
            os.remove("slave.db")

        self.master_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.master_store.initialise()

        self.slave_store = DataStore("", "", "", 0, "slave.db", db_type="sqlite")
        self.slave_store.initialise()

        # Import two files into master
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.master_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "rep_test1.rep"),
            self.master_store,
            False,
        )

        # Import two files into slave
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx"),
            self.slave_store,
            False,
        )
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files", "rep_data", "uk_track.rep"),
            self.slave_store,
            False,
        )

        self.shell = SnapshotShell(self.master_store)

    @patch("pepys_admin.snapshot_cli.ptk_prompt", side_effect=["./slave.db", "y"])
    def test_merge_valid(self, patched_ptk_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.shell.do_merge_databases()
        output = temp_output.getvalue()

        assert "| Platform           |                 0 |       1 |          0 |" in output
        assert "| State       |     402 |" in output

        # Check entries added
        assert "  - uk_track.rep" in output
        assert "  - SPLENDID" in output
        assert "  - SENSOR-1" in output

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    def test_merge_invalid_filename(self, patched_ptk_prompt):
        # Try entering an invalid filename first, then it'll ask us again
        # and so then enter a valid filename
        patched_ptk_prompt.side_effect = ["./nonexisting_file.db", "./slave.db", "y"]

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.shell.do_merge_databases()
        output = temp_output.getvalue()
        print(output)

        assert "| Platform           |                 0 |       1 |          0 |" in output
        assert "| State       |     402 |" in output

        # Check entries added
        assert "  - uk_track.rep" in output
        assert "  - SPLENDID" in output
        assert "  - SENSOR-1" in output

    @patch("pepys_admin.snapshot_cli.ptk_prompt", side_effect=["./slave.db", "n"])
    def test_merge_confirm_no(self, patched_ptk_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.shell.do_merge_databases()
        output = temp_output.getvalue()

        assert "Ok, returning to previous menu" in output

    @patch("pepys_admin.snapshot_cli.custom_print_formatted_text", side_effect=side_effect)
    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    def test_merge_db_not_up_to_date(self, patched_ptk_prompt, patched_print):
        patched_ptk_prompt.side_effect = [
            os.path.join(
                FILE_PATH, "migration_tests", "database", "sqlite", "pepys_0.0.17_test.sqlite"
            )
        ]

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Do the merge
            self.shell.do_merge_databases()
        output = temp_output.getvalue()

        assert (
            "The schema of the selected slave database is not at the latest revision. "
            "Before merging can go ahead you must connect to this database with Pepys Admin and run the 'Migrate' option."
            in output
        )


class TestDatabaseAtLatestRevision(unittest.TestCase):
    def test_db_at_latest_revision_just_alembic_version(self):
        conn = sqlite3.connect("old_alembic_version.sqlite")
        conn.execute(
            """CREATE TABLE alembic_version
(
    version_num VARCHAR(32) NOT NULL
);"""
        )
        conn.execute("""INSERT INTO alembic_version VALUES ("aaaaaaa")""")

        conn.close()

        assert not database_at_latest_revision("old_alembic_version.sqlite")

        if os.path.exists("old_alembic_version.sqlite"):
            os.remove("old_alembic_version.sqlite")

    def test_db_at_latest_revision_no_alembic_version(self):
        conn = sqlite3.connect("no_alembic_version.sqlite")
        conn.execute(
            """CREATE TABLE Blah
(
    TestString VARCHAR(32) NOT NULL
);"""
        )

        conn.close()

        assert not database_at_latest_revision("no_alembic_version.sqlite")

        if os.path.exists("no_alembic_version.sqlite"):
            os.remove("no_alembic_version.sqlite")

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_db_at_latest_revision_uptodate_file(self, patched_prompt):
        store = DataStore("", "", "", 0, "uptodate.sqlite", db_type="sqlite")
        store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data/rep_test1.rep"), store, False
        )
        processor.process(os.path.join(DATA_PATH), store, False)

        assert database_at_latest_revision("uptodate.sqlite")

        if os.path.exists("uptodate.sqlite"):
            os.remove("uptodate.sqlite")

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_db_at_latest_revision_no_json(self, patched_prompt):
        store = DataStore("", "", "", 0, "uptodate.sqlite", db_type="sqlite")
        store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data/rep_test1.rep"), store, False
        )
        processor.process(os.path.join(DATA_PATH), store, False)

        # Rename the latest_revisions.json file as a backup
        move_and_overwrite(
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"),
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json_backup"),
        )

        with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "w") as f:
            f.write("Test")

        assert not database_at_latest_revision("uptodate.sqlite")

        # Rename it back again for future use
        move_and_overwrite(
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json_backup"),
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"),
        )

        if os.path.exists("uptodate.sqlite"):
            os.remove("uptodate.sqlite")

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_db_at_latest_revision_incorrect_json(self, patched_prompt):
        store = DataStore("", "", "", 0, "uptodate.sqlite", db_type="sqlite")
        store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files/rep_data/rep_test1.rep"), store, False
        )
        processor.process(os.path.join(DATA_PATH), store, False)

        # Rename the latest_revisions.json file as a backup
        move_and_overwrite(
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"),
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json_backup"),
        )

        with open(os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"), "w") as f:
            f.write('{"BLAH": "TestValue"}')

        assert not database_at_latest_revision("uptodate.sqlite")

        # Rename it back again for future use
        move_and_overwrite(
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json_backup"),
            os.path.join(MIGRATIONS_DIRECTORY, "latest_revisions.json"),
        )

        if os.path.exists("uptodate.sqlite"):
            os.remove("uptodate.sqlite")

    def test_db_at_latest_version_old_db(self):
        db_path = os.path.join(
            FILE_PATH, "migration_tests", "database", "sqlite", "pepys_0.0.17_test.sqlite"
        )
        assert not database_at_latest_revision(db_path)


class SnapshotShellTestCase(unittest.TestCase):
    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def setUp(self, patched_prompt) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(
            os.path.join(SAMPLE_DATA_PATH, "track_files/other_data"), self.store, False
        )
        processor.process(os.path.join(DATA_PATH), self.store, False)

        with self.store.session_scope():
            self.store.populate_reference()
            change_id = self.store.add_to_changes("TEST", datetime.utcnow(), "test").change_id
            privacy = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter(self.store.db_classes.Privacy.name == "Public")
                .first()
            )
            platform_id = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.privacy_id == privacy.privacy_id)
                .first()
                .platform_id
            )
            privacy_2 = (
                self.store.session.query(self.store.db_classes.Privacy)
                .filter(self.store.db_classes.Privacy.name == "Public Sensitive")
                .first()
            )
            sensor_type = self.store.add_to_sensor_types("SENSOR-TYPE-TEST", change_id)
            nationality = self.store.add_to_nationalities("UK", change_id).name
            platform_type = self.store.add_to_platform_types("PLATFORM-TYPE-1", change_id).name

            platform = self.store.get_platform(
                platform_name="Test Platform",
                identifier="123",
                nationality=nationality,
                platform_type=platform_type,
                privacy=privacy.name,
                change_id=change_id,
            )
            platform.get_sensor(
                self.store,
                "SENSOR-TEST",
                sensor_type=sensor_type.name,
                privacy=privacy_2.name,
                change_id=change_id,
            )
            self.store.add_to_synonyms("Platforms", "test", entity=platform_id, change_id=change_id)

        self.shell = SnapshotShell(self.store)

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    def test_do_export_reference_data(self, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data()
        output = temp_output.getvalue()
        assert "Reference tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM DatafileTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Replay" in names
        assert "GPX" in names
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.custom_print_formatted_text", side_effect=side_effect)
    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    def test_do_export_reference_data_invalid_filename(self, patched_input, patched_print):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        with open("already_existing_file.db", "w") as f:
            f.write("Hello, world")

        patched_input.side_effect = ["already_existing_file.db", "test.db"]
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data()
        output = temp_output.getvalue()

        assert "There is already a file named 'already_existing_file.db'" in output
        assert "Reference tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM DatafileTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Replay" in names
        assert "GPX" in names
        connection.close()

        remove_file_if_exists("test.db")

        if os.path.exists("already_existing_file.db"):
            os.remove("already_existing_file.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public", "Public Sensitive"])
    def test_do_export_reference_data_and_metadata(self, patched_iterfzf, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "SENSOR-1" in names
        assert "New_SSK_FREQ" in names
        assert "E-Trac" in names
        assert "SENSOR-TEST" in names

        results = connection.execute("SELECT * FROM Synonyms;")
        results = results.fetchall()
        table_dict = {row[1]: row[3] for row in results}
        assert "Platforms" in table_dict.keys()
        assert "test" in table_dict.values()
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public"])
    def test_do_export_reference_data_and_metadata_public(self, patched_iterfzf, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "SENSOR-1" in names
        assert "New_SSK_FREQ" in names
        assert "E-Trac" in names
        assert "SENSOR-TEST" not in names

        results = connection.execute("SELECT * FROM Synonyms;")
        results = results.fetchall()
        table_dict = {row[1]: row[3] for row in results}
        assert "Platforms" in table_dict.keys()
        assert "test" in table_dict.values()
        assert "Sensors" not in table_dict.keys()
        assert "test-2" not in table_dict.values()
        connection.close()

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=["Public Sensitive"])
    def test_do_export_reference_data_and_metadata_public_sensitive(
        self, patched_iterfzf, patched_input
    ):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Reference and metadata tables successfully exported!" in output

        connection = sqlite3.connect("test.db")
        results = connection.execute("SELECT name FROM SensorTypes;")
        results = results.fetchall()
        names = [name for r in results for name in r]
        assert "Location-Satellite" in names
        assert "Position" in names

        # Even though there are Sensor objects with Public Sensitive level, their Platform objects
        # have different privacy values. Therefore, none of platforms and sensors are exported.
        results = connection.execute("SELECT name FROM Sensors;")
        results = results.fetchall()
        assert len(results) == 0
        connection.close()

        remove_file_if_exists("test.db")

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text", side_effect=side_effect)
    def test_default(self, patched_print):
        # Only cancel command (0) returns True, others return None
        result = self.shell.default(".")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    @patch("pepys_admin.base_cli.custom_print_formatted_text")
    def test_postcmd(self, patched_print):
        patched_print.side_effect = side_effect
        # postcmd method should print the menu again if the user didn't select cancel (".")
        # Select Create snapshot with Reference data
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.postcmd(stop=None, line="1")
        output = temp_output.getvalue()
        assert self.shell.choices in output
        # Select Create snapshot with Reference data & Metadata
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.postcmd(stop=None, line="2")
        output = temp_output.getvalue()
        assert self.shell.choices in output

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    @patch("pepys_admin.snapshot_cli.iterfzf", return_value=None)
    def test_do_export_reference_and_metadata_cancelling(self, patched_iterfzf, patched_input):
        # Delete test.db file first, in case it is hanging around from another test
        # If we don't do this, we can get into an infinite loop
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_reference_data_and_metadata()
        output = temp_output.getvalue()
        assert "Returning to the previous menu" in output

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt", return_value="test.db")
    def test_do_export_all_data(self, patched_ptkprompt):
        remove_file_if_exists("test.db")

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_all_data()
        output = temp_output.getvalue()
        assert "Data successfully exported" in output

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.prompt")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_time")
    def test_do_export_all_data_filter_time(
        self, patched_export, patched_prompt, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        patched_prompt.side_effect = ["2000-01-01 00:00:00", "2005-05-25 00:00:00"]
        patched_db_prompt.side_effect = ["test.db"]

        self.shell.do_export_all_data_filter_time()

        patched_export.assert_called_with(
            ANY, ANY, datetime(2000, 1, 1, 0, 0), datetime(2005, 5, 25, 0, 0)
        )

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.prompt")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_time")
    def test_do_export_all_data_filter_time_invalid_type(
        self, patched_export, patched_prompt, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        patched_prompt.side_effect = ["abcd", "2000-01-01 00:00:00", "2005-05-25 00:00:00"]
        patched_db_prompt.side_effect = ["test.db"]

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_all_data_filter_time()
        output = temp_output.getvalue()
        assert "Invalid time entered, please try again" in output

        patched_export.assert_called_with(
            ANY, ANY, datetime(2000, 1, 1, 0, 0), datetime(2005, 5, 25, 0, 0)
        )

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.prompt")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_time")
    def test_do_export_all_data_filter_time_invalid_date(
        self, patched_export, patched_prompt, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        patched_prompt.side_effect = [
            "2000-15-50 00:00:00",
            "2000-01-01 00:00:00",
            "2005-05-25 00:00:00",
        ]
        patched_db_prompt.side_effect = ["test.db"]

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_all_data_filter_time()
        output = temp_output.getvalue()
        assert "Invalid time entered, please try again" in output

        patched_export.assert_called_with(
            ANY, ANY, datetime(2000, 1, 1, 0, 0), datetime(2005, 5, 25, 0, 0)
        )

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.prompt")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_location")
    def test_do_export_all_data_filter_location(
        self, patched_export, patched_prompt, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        patched_prompt.side_effect = ["0", "40", "-10", "10"]
        patched_db_prompt.side_effect = ["test.db"]

        self.shell.do_export_all_data_filter_location()

        patched_export.assert_called_with(ANY, ANY, -10, 0, 10, 40)

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.prompt")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_location")
    def test_do_export_all_data_filter_location_invalid(
        self, patched_export, patched_prompt, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        patched_prompt.side_effect = ["abc", "0", "40", "-10", "10"]
        patched_db_prompt.side_effect = ["test.db"]

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_export_all_data_filter_location()
        output = temp_output.getvalue()
        assert "Invalid number entered, please try again" in output

        patched_export.assert_called_with(ANY, ANY, -10, 0, 10, 40)

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_helpers.iterfzf")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_wargame_participation")
    def test_do_export_all_data_filter_wargame(
        self, patched_export, patched_iterfzf, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        with self.store.session_scope():
            priv_id = self.store.session.query(self.store.db_classes.Privacy).all()[0].privacy_id
            change_id = self.store.add_to_changes(
                "USER", datetime.utcnow(), "Creating test tasks/participants"
            ).change_id
            s1 = self.store.db_classes.Series(name="Test Series", privacy_id=priv_id)

            wg1 = self.store.db_classes.Wargame(
                name="Test Wargame",
                start=datetime(2000, 1, 1),
                end=datetime(2000, 2, 1),
                privacy_id=priv_id,
            )
            wg1.series = s1

            self.store.session.add_all([s1, wg1])

            plat1 = (
                self.store.session.query(self.store.db_classes.Platform)
                .filter(self.store.db_classes.Platform.name == "Test Platform")
                .one()
            )

            wg1.add_participant(
                data_store=self.store, platform=plat1, privacy="Private", change_id=change_id
            )

        patched_iterfzf.side_effect = ["Test Wargame"]
        patched_db_prompt.side_effect = ["test.db"]

        self.shell.do_export_all_data_filter_wargame_participation()

        patched_export.assert_called_once()
        assert patched_export.call_args[0][-1].name == "Test Wargame"

        remove_file_if_exists("test.db")

    @patch("pepys_admin.snapshot_cli.ptk_prompt")
    @patch("pepys_admin.snapshot_cli.iterfzf")
    @patch("pepys_admin.snapshot_helpers.iterfzf")
    @patch("pepys_admin.snapshot_cli.export_measurement_tables_filtered_by_serial_participation")
    def test_do_export_all_data_filter_serial(
        self, patched_export, patched_iterfzf, patched_iterfzf2, patched_db_prompt
    ):
        remove_file_if_exists("test.db")

        with self.store.session_scope():
            priv_id = self.store.session.query(self.store.db_classes.Privacy).all()[0].privacy_id
            s1 = self.store.db_classes.Series(name="Test Series", privacy_id=priv_id)

            wg1 = self.store.db_classes.Wargame(
                name="Test Wargame",
                start=datetime(2000, 1, 1),
                end=datetime(2000, 2, 1),
                privacy_id=priv_id,
            )
            wg1.series = s1

            self.store.session.add_all([s1, wg1])

            serial1 = self.store.db_classes.Serial(
                serial_number="Test Serial",
                exercise="Test Exercise",
                start=datetime(2000, 1, 5),
                end=datetime(2000, 1, 10),
                environment="Test Environment",
                privacy_id=priv_id,
            )

            serial1.wargame = wg1

            self.store.session.add(serial1)

        patched_iterfzf.side_effect = ["Test Wargame"]
        patched_iterfzf2.side_effect = ["Test Serial"]
        patched_db_prompt.side_effect = ["test.db"]

        self.shell.do_export_all_data_filter_serial_participation()

        patched_export.assert_called_once()
        assert patched_export.call_args[0][-1].serial_number == "Test Serial"

        remove_file_if_exists("test.db")


@patch("pepys_admin.base_cli.custom_print_formatted_text")
@patch("cmd.input")
@patch("pepys_admin.cli.prompt")
@patch("pepys_import.cli.prompt")
def test_training_mode_message(patched_prompt1, patched_prompt2, patched_input, patched_print):
    patched_print.side_effect = side_effect
    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    patched_prompt1.side_effect = ["n"]
    patched_prompt2.side_effect = ["n"]

    # When asked for input, choose to exit
    patched_input.side_effect = ["."]

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        try:
            run_shell(db=None, training=True, path=".")
        except SystemExit:
            pass
    output = temp_output.getvalue()
    print(output)

    assert "Running in Training Mode" in output

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_admin.base_cli.custom_print_formatted_text")
@patch("pepys_admin.cli.DataStore")
@patch("cmd.input")
@patch("pepys_admin.cli.prompt")
@patch("pepys_import.cli.prompt")
def test_training_mode_setup(
    patched_prompt1, patched_prompt2, patched_input, patched_data_store, patched_print
):
    patched_print.side_effect = side_effect
    # Store original PEPYS_CONFIG_FILE variable so we can reset it at the end
    # (as setting training mode changes that for this process - and when
    # pytest is running tests it runs them all in one process)
    orig_pepys_config_file = os.environ.get("PEPYS_CONFIG_FILE")

    patched_prompt1.side_effect = ["n"]
    patched_prompt2.side_effect = ["n"]

    patched_input.side_effect = ["."]

    db_name = os.path.expanduser(
        os.path.join("~", "Pepys_Training_Data", "pepys_training_database.db")
    )

    try:
        run_shell(db=None, training=True, path=".")
    except SystemExit:
        pass

    # Check it is called with the right db path, and with training_mode=True
    patched_data_store.assert_called_with(
        db_username="",
        db_password="",
        db_host="",
        db_port=0,
        db_name=db_name,
        db_type="sqlite",
        welcome_text="Pepys_admin",
    )

    # Reset PEPYS_CONFIG_FILE to what it was at the start of the test
    if orig_pepys_config_file is None:
        del os.environ["PEPYS_CONFIG_FILE"]
    else:
        os.environ["PEPYS_CONFIG_FILE"] = orig_pepys_config_file


@patch("pepys_admin.cli.DataStore")
def test_viewer_mode_datastore(patched_ds):
    run_shell(path=".", db=None, training=False, viewer=True)

    patched_ds.assert_called_with(
        db_username=ANY,
        db_password=ANY,
        db_host=ANY,
        db_port=ANY,
        db_name=ANY,
        db_type=ANY,
        welcome_text="Pepys_viewer",
    )


@patch("pepys_admin.cli.custom_print_formatted_text", side_effect=side_effect)
def test_viewer_mode_blank_db(patched_print):
    temp_output = StringIO()
    with redirect_stdout(temp_output):
        try:
            run_shell(path=".", db=":memory:", training=False, viewer=True)
        except SystemExit:
            pass
    output = temp_output.getvalue()
    print(output)

    assert "Database schema does not exist: tables cannot be viewed" in output


@patch("pepys_admin.cli.ViewerShell")
def test_viewer_mode_valid_db(patched_vs):
    if os.path.exists("created_db.db"):
        os.remove("created_db.db")

    store = DataStore("", "", "", 0, "created_db.db", db_type="sqlite")
    store.initialise()

    run_shell(path=".", db="created_db.db", training=False, viewer=True)

    patched_vs.assert_called()


def remove_file_if_exists(filename):
    path = os.path.join(CURRENT_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
