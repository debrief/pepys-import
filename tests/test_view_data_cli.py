import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")


class ViewDataCLITestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.shell = ViewDataShell(self.store)

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="Datafiles")
    def test_do_view_table(self, patched_input):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_view_table()
        output = temp_output.getvalue()
        print(output)
        assert "Datafiles\n" in output
        assert "| datafile_type_name   | reference                        | url   |\n" in output
        assert "| E-Trac               | e_trac_bad.txt                   | None  |\n" in output
        assert "| E-Trac               | e_trac.txt                       | None  |\n" in output
        assert "| EAG                  | 20200305_ROBIN.eag.txt           | None  |" in output
        assert "| NMEA                 | NMEA_bad.log                     | None  |" in output

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="alembic_version")
    def test_do_view_table_alembic_version(self, patched_input):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_view_table()
        output = temp_output.getvalue()
        assert "Alembic Version\n" in output
        assert "| version_number   |" in output

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT * FROM Datafiles;")
    def test_do_run_sql(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_run_sql()
        output = temp_output.getvalue()
        print(output)
        assert "SELECT * FROM Datafiles;" in output
        assert (
            "| e_trac_bad.txt                   | None | 5261 | 7bbe513d9d253d2277435e0849ed8342"
            in output
        )
        assert (
            "| e_trac.txt                       | None | 5315 | 577fad568cda2eb0b24178f5554f2b46"
            in output
        )
        assert (
            "| NMEA_bad.log                     | None |  243 | 8ddb840fee218872d2bb394cc654bdae"
            in output
        )

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT Blah from NonExisting")
    def test_do_run_sql_invalid(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_run_sql()
        output = temp_output.getvalue()
        print(output)
        assert "ERROR: Query couldn't be executed successfully" in output

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output

    def test_default(self):
        # Only cancel command (0) returns True, others return None
        result = self.shell.default(".")
        assert result is True

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.default("123456789")
        output = temp_output.getvalue()
        assert "*** Unknown syntax: 123456789" in output

    def test_postcmd(self):
        # postcmd method should print the menu again if the user didn't select cancel (".")
        # Select view table
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.postcmd(stop=False, line="1")
        output = temp_output.getvalue()
        assert self.shell.intro in output
        # Select run sql
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.postcmd(stop=False, line="2")
        output = temp_output.getvalue()
        assert self.shell.intro in output


if __name__ == "__main__":
    unittest.main()
