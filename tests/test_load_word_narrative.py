import os
import unittest
from unittest.mock import patch

from importers.word_narrative_importer import WordNarrativeImporter
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/word/Narrative Example.docx")


class TestLoadWordNarrative(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()

    def tearDown(self):
        pass

    @patch("pepys_import.core.store.common_db.prompt", return_value="2")
    def test_load_word_data(self, patched_prompt):
        processor = FileProcessor(archive=False)
        processor.register_importer(WordNarrativeImporter())

        # check states empty
        with self.store.session_scope():
            # there must be no states at the beginning
            states = self.store.session.query(self.store.db_classes.State).all()
            self.assertEqual(len(states), 0)

            # there must be no platforms at the beginning
            platforms = self.store.session.query(self.store.db_classes.Platform).all()
            self.assertEqual(len(platforms), 0)

            # there must be no datafiles at the beginning
            datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
            self.assertEqual(len(datafiles), 0)

        # parse the file
        processor.process(DATA_PATH, self.store, False)

        # # check data got created
        # with self.store.session_scope():
        #     # there must be states after the import
        #     states = self.store.session.query(self.store.db_classes.State).all()
        #     self.assertEqual(len(states), 746)

        #     # there must be platforms after the import
        #     platforms = self.store.session.query(self.store.db_classes.Platform).all()
        #     self.assertEqual(len(platforms), 5)

        #     # there must be one datafile afterwards
        #     datafiles = self.store.session.query(self.store.db_classes.Datafile).all()
        #     self.assertEqual(len(datafiles), 6)

        #     # There should be one state with no elevation, which comes from the NaN
        #     # in the elevation field in the first line of uk_track.rep
        #     states_with_no_elevation = (
        #         self.store.session.query(self.store.db_classes.State)
        #         .filter(self.store.db_classes.State.elevation.is_(None))
        #         .all()
        #     )

        #     assert len(states_with_no_elevation) == 1

        #     # This state should have a time of
        #     assert states_with_no_elevation[0].time == datetime.datetime(2018, 5, 7, 5, 0, 0)

        #     # there should be 581 points with an elevation of 0m
        #     # (this proves that zero values are imported properly and not
        #     # treated as errors)
        #     elev_zero_states = (
        #         self.store.session.query(self.store.db_classes.State)
        #         .filter(self.store.db_classes.State.elevation == 0)
        #         .all()
        #     )
        #     assert len(elev_zero_states) == 581


if __name__ == "__main__":
    unittest.main()
