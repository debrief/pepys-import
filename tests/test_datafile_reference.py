import unittest
import os

from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary
from pepys_import.file.file_processor import FileProcessor
from importers.replay_importer import ReplayImporter

DIRECTORY_PATH = os.path.dirname(__file__)
REP_FILE_PATH = os.path.join(
    DIRECTORY_PATH, "sample_data/track_files/rep_data/rep_test1.rep"
)


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


if __name__ == "__main__":
    unittest.main()
