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
        assert "Datafiles\n" in output
        assert (
            "|   datafile_id | reference      | url   |   size | privacy_name   | datafile_type_name   |\n"
            in output
        )
        assert (
            "| e_trac_bad.txt | None  |   5261 | PRIVACY-1      | .txt                 |\n"
            in output
        )
        assert (
            "| e_trac.txt     | None  |   5315 | PRIVACY-1      | .txt                 |\n"
            in output
        )
        assert (
            "| NMEA_bad.log   | None  |    243 | Private        | .log                 |" in output
        )

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT * FROM Datafiles;")
    def test_do_run_sql(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_run_sql()
        output = temp_output.getvalue()
        assert "SELECT * FROM Datafiles;" in output
        assert "| e_trac_bad.txt | None | 5261 | 47e7c07157672a353a112ffbc033571d" in output
        assert "| e_trac.txt     | None | 5315 | 577fad568cda2eb0b24178f5554f2b46" in output
        assert "| NMEA_bad.log   | None |  243 | 8ddb840fee218872d2bb394cc654bdae" in output

    def test_do_cancel(self):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_cancel()
        output = temp_output.getvalue()
        assert "Returning to the previous menu..." in output


if __name__ == "__main__":
    unittest.main()
