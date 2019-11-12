import unittest
import os

from geoalchemy2 import WKBElement, WKTElement

from pepys_import.core.store.data_store import DataStore

FILE_PATH = os.path.dirname(__file__)
TEST_DATA_PATH = os.path.join(FILE_PATH, "sample_data", "csv_files")


class SpatialDataTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
        self.store.initialise()
        self.store.populate_reference(TEST_DATA_PATH)
        self.store.populate_metadata(TEST_DATA_PATH)
        self.store.populate_measurement(TEST_DATA_PATH)

    def tearDown(self) -> None:
        pass

    def test_location(self):
        with self.store.session_scope() as session:
            # Filter state object by spatial location
            first_state = (
                self.store.session.query(self.store.db_classes.State)
                .filter(
                    self.store.db_classes.State.location.ST_Contains(
                        WKTElement("POINT(46.000 32.000)")
                    )
                )
                .first()
            )

            # Check location point's type and WKTE value
            self.assertTrue(isinstance(first_state.location, WKBElement))
            self.assertEqual(
                first_state.location.data,
                "0101000020FFFFFFFF00000000000047400000000000004040",
            )


if __name__ == "__main__":
    unittest.main()
