import os
import unittest
from datetime import datetime

from pepys_admin.snapshot_helpers import (
    export_all_measurement_tables,
    export_measurement_tables_filtered_by_time,
    export_metadata_tables,
    export_reference_tables,
)
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table

FILE_PATH = os.path.dirname(__file__)
NISIDA_PATH = os.path.join(FILE_PATH, "sample_data/track_files/nisida/nisida_example.txt")


class TestSnapshots(unittest.TestCase):
    def setUp(self):
        if os.path.exists("destination.db"):
            os.remove("destination.db")

        self.source_store = DataStore("", "", "", 0, db_name="source.db", db_type="sqlite")
        self.source_store.initialise()
        with self.source_store.session_scope():
            self.source_store.populate_reference()
            self.source_store.populate_metadata()

        processor = FileProcessor(archive=False)
        processor.load_importers_dynamically()
        processor.process(NISIDA_PATH, self.source_store, False)

        self.destination_store = DataStore(
            "",
            "",
            "",
            0,
            db_name="destination.db",
            db_type="sqlite",
            show_status=False,
            welcome_text=None,
        )
        self.destination_store.initialise()

        # Export reference tables
        reference_table_objects = self.source_store.meta_classes[TableTypes.REFERENCE]
        export_reference_tables(self.source_store, self.destination_store, reference_table_objects)

        # Export metadata tables
        export_metadata_tables(self.source_store, self.destination_store)

    def tearDown(self):
        if os.path.exists("source.db"):
            os.remove("source.db")

        if os.path.exists("destination.db"):
            os.remove("destination.db")

    def _check_tables_equal(self, tables):
        for table in tables:
            print(f"Table = {table}")
            source_table = getattr(self.source_store.db_classes, table)
            source_values = self.source_store.session.query(source_table).all()
            source_count = len(source_values)

            destination_table = getattr(self.destination_store.db_classes, table)
            destination_values = self.destination_store.session.query(destination_table).all()
            destination_count = len(destination_values)

            assert source_count == destination_count

            source_ids = [
                getattr(item, get_primary_key_for_table(source_table)) for item in source_values
            ]
            destination_ids = [
                getattr(item, get_primary_key_for_table(destination_table))
                for item in destination_values
            ]

            assert set(source_ids) == set(destination_ids)

    def test_export_all(self):
        export_all_measurement_tables(self.source_store, self.destination_store)
        self._check_tables_equal(
            [
                "State",
                "Contact",
                "Comment",
                "Activation",
                "LogsHolding",
                "Geometry1",
                "Media",
            ]
        )

    def test_export_filtered_by_time_with_time_field_1(self):
        # Start is part-way through measurements, so only some should be exported
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 10, 31, 10, 45),
            datetime(2004, 1, 1),
        )

        # Check State table has only two items left in it now
        state_entries = self.destination_store.session.query(
            self.destination_store.db_classes.State
        ).all()
        assert len(state_entries) == 2
        times = [entry.time for entry in state_entries]
        assert times == [datetime(2003, 10, 31, 12, 0), datetime(2003, 10, 31, 12, 6)]

        comment_entries = self.destination_store.session.query(
            self.destination_store.db_classes.Comment
        ).all()
        assert len(comment_entries) == 6
        times = [entry.time for entry in comment_entries]
        assert times == [
            datetime(2003, 10, 31, 10, 56),
            datetime(2003, 10, 31, 11, 0),
            datetime(2003, 10, 31, 12, 6),
            datetime(2003, 10, 31, 12, 12),
            datetime(2003, 10, 31, 13, 5),
            datetime(2003, 10, 31, 21, 0),
        ]

    def test_export_filtered_by_time_with_time_field_2(self):
        # Both start and end are before any of the measurements, so everything should
        # be exported
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 9, 1, 10, 23),
            datetime(2004, 9, 5, 16, 45),
        )

        self._check_tables_equal(
            [
                "State",
                "Contact",
                "Comment",
                "LogsHolding",
                "Media",
            ]
        )
