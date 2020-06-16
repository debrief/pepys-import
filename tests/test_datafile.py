import os
import shutil
import unittest
from contextlib import redirect_stdout
from io import StringIO

from importers.replay_importer import ReplayImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.datafile_utils import hash_file

DIRECTORY_PATH = os.path.dirname(__file__)
CURRENT_DIR = os.getcwd()
REP_DATA_PATH = os.path.join(DIRECTORY_PATH, "sample_data", "track_files", "rep_data")
REP_FILE_PATH = os.path.join(REP_DATA_PATH, "rep_test1.rep")


class ReferenceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def test_filename_is_correct(self):
        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())

        with self.store.session_scope():
            datafiles = TableSummary(self.store.session, self.store.db_classes.Datafile)
            assert datafiles.number_of_rows == 0

        processor.process(REP_FILE_PATH, self.store, False)

        with self.store.session_scope():
            datafiles = TableSummary(self.store.session, self.store.db_classes.Datafile)
            assert datafiles.number_of_rows == 1

            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            assert datafiles[0].reference == "rep_test1.rep"


class DuplicatedFilesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, "test.db", db_type="sqlite")
        self.store.initialise()
        self.processor = FileProcessor()
        self.processor.register_importer(ReplayImporter())

    def tearDown(self) -> None:
        test_db = os.path.join(CURRENT_DIR, "test.db")
        if os.path.exists(test_db):
            os.remove(test_db)

    def test_importing_the_same_file_twice(self):
        """Test whether process method runs only once when the same datafile is given"""
        # Process the rep file
        self.processor.process(REP_FILE_PATH, self.store, False)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Try to process the same file again
            self.processor.process(REP_FILE_PATH, self.store, False)
        output = temp_output.getvalue()

        assert "Files got processed: 0 times" in output
        assert "'rep_test1.rep' was already loaded" in output

    def test_importing_the_same_file_with_different_name(self):
        """Test whether process method runs only once when the same datafile
        with a different name is given"""
        copied_file_path = os.path.join(REP_DATA_PATH, "copy_rep_test1.rep")
        # Copy file
        shutil.copyfile(REP_FILE_PATH, copied_file_path)

        # Process the rep file
        self.processor.process(REP_FILE_PATH, self.store, False)

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Try to process the copied file
            self.processor.process(copied_file_path, self.store, False)
        output = temp_output.getvalue()

        assert "Files got processed: 0 times" in output
        assert "'rep_test1.rep' was already loaded" in output
        # Delete the copy file
        os.remove(copied_file_path)

    def test_importing_modified_file(self):
        """Test whether process method imports the datafile when some lines removed from it"""
        copied_file_path = os.path.join(REP_DATA_PATH, "modified_rep_test1.rep")
        # Copy file
        shutil.copyfile(REP_FILE_PATH, copied_file_path)
        # Delete characters from the copy file
        with open(copied_file_path, "r") as file:
            lines = file.readlines()
        # Strip first and last two lines, write it to the same file
        with open(copied_file_path, "w") as file:
            file.writelines(lines[2:-2])

        # Assert that file size is changed
        assert os.stat(copied_file_path).st_size != os.stat(REP_FILE_PATH).st_size

        # Process the rep file
        self.processor.process(REP_FILE_PATH, self.store, False)

        # Query Datafile table, it should have one entity
        datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
        assert len(datafiles) == 1
        assert datafiles[0].reference == "rep_test1.rep"

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Try to process the modified file
            self.processor.process(copied_file_path, self.store, False)
        output = temp_output.getvalue()
        # Assert that file is processed
        assert "Files got processed: 1 times" in output
        # Query Datafile table, it should have two entities now
        datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
        assert len(datafiles) == 2
        assert datafiles[1].reference == "modified_rep_test1.rep"

        # Delete the copy file
        os.remove(copied_file_path)

    def test_importing_modified_file_alternative(self):
        """Test whether process method imports the datafile
        when some characters of datafile is changed"""
        copied_file_path = os.path.join(REP_DATA_PATH, "modified_rep_test1.rep")
        # Copy file
        shutil.copyfile(REP_FILE_PATH, copied_file_path)
        # Delete characters from the copy file
        with open(copied_file_path, "r") as file:
            lines = file.readlines()
        # Change characters
        lines[0] = lines[0].replace("A", "x")
        lines[0] = lines[0].replace("B", "y")
        # Strip first and last two lines, write it to the same file
        with open(copied_file_path, "w") as file:
            file.writelines(lines)

        # Assert that file hash is changed and file size is the same
        assert os.stat(copied_file_path).st_size == os.stat(REP_FILE_PATH).st_size
        assert hash_file(copied_file_path) != hash_file(REP_FILE_PATH)

        # Process the rep file
        self.processor.process(REP_FILE_PATH, self.store, False)

        # Query Datafile table, it should have one entity
        datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
        assert len(datafiles) == 1
        assert datafiles[0].reference == "rep_test1.rep"

        temp_output = StringIO()
        with redirect_stdout(temp_output):
            # Try to process the modified file
            self.processor.process(copied_file_path, self.store, False)
        output = temp_output.getvalue()
        # Assert that file is processed
        assert "Files got processed: 1 times" in output
        # Query Datafile table, it should have two entities now
        datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
        assert len(datafiles) == 2
        assert datafiles[1].reference == "modified_rep_test1.rep"

        # Delete the copy file
        os.remove(copied_file_path)


if __name__ == "__main__":
    unittest.main()
