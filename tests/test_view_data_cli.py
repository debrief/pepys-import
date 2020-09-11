import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from sqlalchemy.exc import OperationalError
from testing.postgresql import Postgresql

from pepys_admin.view_data_cli import ViewDataShell
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/other_data")
CURRENT_DIR = os.getcwd()


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

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="Datafiles")
    def test_do_output_table_to_csv(self, patched_input):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_Datafiles.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_table_to_csv()
        output = temp_output.getvalue()
        assert "Datafiles table is successfully exported!" in output
        assert f"You can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert (
                    "datafile_id,simulated,privacy_id,datafile_type_id,reference,url,size,hash,created_date\n"
                    in data
                )
                assert "e_trac_bad.txt,,5261,7bbe513d9d253d2277435e0849ed8342" in data
                assert "20200305_ROBIN.eag.txt,,386,f3d0a8a1760f312ea57912548b48b766" in data
                assert (
                    "20200305_ROBINWithHeader.eag.txt,,479,ec2694c2cfe2eaa26181999a55aee5b4" in data
                )
                assert "rep_duplicate_name_test.rep,,153,4e8067e51a8e39b2a8fd9f9802618247" in data

            os.remove(path)

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="alembic_version")
    def test_do_output_table_to_csv_alembic_version(self, patched_input):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_alembic_version.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_table_to_csv()
        output = temp_output.getvalue()
        assert "alembic_version table is successfully exported!" in output
        assert f"You can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert "version_num\n" in data

            os.remove(path)

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
            "| NMEA_bad.log                     | None |  243 | b201a229fb2c4a80bd657066e4bf9c8a"
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

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT * FROM Datafiles;")
    def test_do_output_sql_to_csv(self, patched_prompt):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_SQL_Query.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_sql_to_csv()
        output = temp_output.getvalue()
        assert f"SQL results are successfully exported!\nYou can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert "Executed Query: SELECT * FROM Datafiles;" in data
                assert "e_trac_bad.txt,,5261,7bbe513d9d253d2277435e0849ed8342" in data
                assert "20200305_ROBIN.eag.txt,,386,f3d0a8a1760f312ea57912548b48b766" in data
                assert (
                    "20200305_ROBINWithHeader.eag.txt,,479,ec2694c2cfe2eaa26181999a55aee5b4" in data
                )
                assert "rep_duplicate_name_test.rep,,153,4e8067e51a8e39b2a8fd9f9802618247" in data

            os.remove(path)

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT Blah from NonExisting")
    def test_do_output_sql_to_csv_invalid(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_sql_to_csv()
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
        # Only cancel command (.) returns True, others return None
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


class ViewDataCLIPostgresTestCase(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.postgres = Postgresql(
                database="test",
                host="localhost",
                user="postgres",
                password="postgres",
                port=55527,
            )
        except RuntimeError:
            print("PostgreSQL database couldn't be created! Test is skipping.")
            return
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
            print("Database schema and data population failed! Test is skipping.")

        # Parse the REP files
        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(DATA_PATH, self.store, False)

        self.shell = ViewDataShell(self.store)

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

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

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="Datafiles")
    def test_do_output_table_to_csv(self, patched_input):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_Datafiles.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_table_to_csv()
        output = temp_output.getvalue()
        assert "Datafiles table is successfully exported!" in output
        assert f"You can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert (
                    "datafile_id,simulated,privacy_id,datafile_type_id,reference,url,size,hash,created_date\n"
                    in data
                )
                assert "e_trac_bad.txt,,5261,7bbe513d9d253d2277435e0849ed8342" in data
                assert "20200305_ROBIN.eag.txt,,386,f3d0a8a1760f312ea57912548b48b766" in data
                assert (
                    "20200305_ROBINWithHeader.eag.txt,,479,ec2694c2cfe2eaa26181999a55aee5b4" in data
                )
                assert "rep_duplicate_name_test.rep,,153,4e8067e51a8e39b2a8fd9f9802618247" in data

            os.remove(path)

    @patch("pepys_admin.view_data_cli.iterfzf", return_value="alembic_version")
    def test_do_output_table_to_csv_alembic_version(self, patched_input):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_alembic_version.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_table_to_csv()
        output = temp_output.getvalue()
        assert "alembic_version table is successfully exported!" in output
        assert f"You can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert "version_num\n" in data

            os.remove(path)

    @patch("pepys_admin.view_data_cli.prompt", return_value='SELECT * FROM "pepys"."Datafiles";')
    def test_do_run_sql(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_run_sql()
        output = temp_output.getvalue()
        print(output)
        assert 'SELECT * FROM "pepys"."Datafiles";' in output
        assert (
            "| e_trac_bad.txt                   | None | 5261 | 7bbe513d9d253d2277435e0849ed8342"
            in output
        )
        assert (
            "| e_trac.txt                       | None | 5315 | 577fad568cda2eb0b24178f5554f2b46"
            in output
        )
        assert (
            "| NMEA_bad.log                     | None |  243 | b201a229fb2c4a80bd657066e4bf9c8a"
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

    @patch("pepys_admin.view_data_cli.prompt", return_value='SELECT * FROM "pepys"."Datafiles";')
    def test_do_output_sql_to_csv(self, patched_prompt):
        path = os.path.join(CURRENT_DIR, "Pepys_Output_SQL_Query.csv")
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_sql_to_csv()
        output = temp_output.getvalue()
        assert f"SQL results are successfully exported!\nYou can find it here: '{path}'." in output

        if os.path.exists(path):
            with open(path, "r") as f:
                data = f.read()
                assert 'Executed Query: SELECT * FROM ""pepys"".""Datafiles"";' in data
                assert "rep_duplicate_name_test.rep,,153,4e8067e51a8e39b2a8fd9f9802618247" in data
                assert (
                    "20200305_ROBINWithHeader.eag.txt,,479,ec2694c2cfe2eaa26181999a55aee5b4" in data
                )
                assert "e_trac_bad.txt,,5261,7bbe513d9d253d2277435e0849ed8342" in data
                assert "e_trac.txt,,5315,577fad568cda2eb0b24178f5554f2b46" in data

            os.remove(path)

    @patch("pepys_admin.view_data_cli.prompt", return_value="SELECT Blah from NonExisting")
    def test_do_output_sql_to_csv_invalid(self, patched_prompt):
        temp_output = StringIO()
        with redirect_stdout(temp_output):
            self.shell.do_output_sql_to_csv()
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
        # Only cancel command (.) returns True, others return None
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
