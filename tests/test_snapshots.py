import os
import unittest
from datetime import datetime

from pepys_admin.snapshot_helpers import (
    export_all_measurement_tables,
    export_measurement_tables_filtered_by_location,
    export_measurement_tables_filtered_by_serial_participation,
    export_measurement_tables_filtered_by_time,
    export_measurement_tables_filtered_by_wargame_participation,
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
        with self.source_store.session_scope():
            with self.destination_store.session_scope():
                for table in tables:
                    print(f"Table = {table}")
                    source_table = getattr(self.source_store.db_classes, table)
                    source_values = self.source_store.session.query(source_table).all()
                    source_count = len(source_values)

                    destination_table = getattr(self.destination_store.db_classes, table)
                    destination_values = self.destination_store.session.query(
                        destination_table
                    ).all()
                    destination_count = len(destination_values)

                    assert source_count == destination_count

                    source_ids = [
                        getattr(item, get_primary_key_for_table(source_table))
                        for item in source_values
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

        with self.source_store.session_scope():
            with self.destination_store.session_scope():
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

    def _check_start_end_times(self, results, correct_start_end_times):
        def _parse(s):
            if s is None:
                return None
            else:
                return datetime.strptime(s, "%Y-%m-%d %H:%M")

        start_end_times = [(a.start, a.end) for a in results]

        parsed_correct_start_end_times = [
            (_parse(a), _parse(b)) for (a, b) in correct_start_end_times
        ]

        assert set(start_end_times) == set(parsed_correct_start_end_times)

    def test_export_filtered_by_time_start_and_end_field_1(self):
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 10, 31, 12, 00),
            datetime(2004, 11, 1, 12, 00),
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 2

            self._check_start_end_times(
                results, [("2003-10-31 13:00", "2003-10-31 14:50"), (None, "2003-10-31 15:00")]
            )

    def test_export_filtered_by_time_start_and_end_field_2(self):
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 10, 31, 10, 1),
            datetime(2003, 10, 31, 11, 2),
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 2

            self._check_start_end_times(
                results, [("2003-10-31 10:02", None), ("2003-10-31 11:00", "2003-10-31 11:03")]
            )

    def test_export_filtered_by_time_start_and_end_field_3(self):
        # Before all activation entries, so no results should be returned
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 9, 1, 10, 1),
            datetime(2003, 9, 2, 11, 2),
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 0

    def test_export_filtered_by_time_start_and_end_field_4(self):
        # After all activation entries, so no results should be returned
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 12, 31, 10, 1),
            datetime(2003, 12, 31, 11, 2),
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 0

    def test_export_filtered_by_time_start_and_end_field_5(self):
        export_measurement_tables_filtered_by_time(
            self.source_store,
            self.destination_store,
            datetime(2003, 10, 31, 9, 30),
            datetime(2003, 10, 31, 14, 0),
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 4

            self._check_start_end_times(
                results,
                [
                    ("2003-10-31 10:02", None),
                    ("2003-10-31 13:00", "2003-10-31 14:50"),
                    ("2003-10-31 10:00", None),
                    ("2003-10-31 11:00", "2003-10-31 11:03"),
                ],
            )

    def test_export_filtered_by_location_no_overlap(self):
        export_measurement_tables_filtered_by_location(
            self.source_store, self.destination_store, -90, 0, -85, 10
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.State
            ).all()

            assert len(results) == 0

    def test_export_filtered_by_location_partial_overlap(self):
        export_measurement_tables_filtered_by_location(
            self.source_store, self.destination_store, 4.1, 36, 4.3, 37
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.State
            ).all()

            assert len(results) == 2

            times = [s.time for s in results]
            assert times == [
                datetime(2003, 10, 31, 10, 2),
                datetime(2003, 10, 31, 12, 0),
            ]

    def test_export_filtered_by_location_complete_overlap(self):
        export_measurement_tables_filtered_by_location(
            self.source_store, self.destination_store, 2, 30, 7, 40
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.State
            ).all()

            assert len(results) == 5

    def test_export_filtered_by_wargame_no_overlap(self):
        # Create wargame and participants with wargame times
        # not overlapping with any data
        wg = self._create_wargame(start_time=datetime(2000, 1, 1), end_time=datetime(2000, 2, 1))

        export_measurement_tables_filtered_by_wargame_participation(
            self.source_store, self.destination_store, wg
        )

        with self.destination_store.session_scope():
            for table in ["State", "Comment", "Contact", "Activation"]:
                results = self.destination_store.session.query(
                    getattr(self.destination_store.db_classes, table)
                ).all()

                assert len(results) == 0

    def test_export_filtered_by_wargame_with_overlap(self):
        wg = self._create_wargame(
            start_time=datetime(2003, 10, 31, 11, 0), end_time=datetime(2003, 11, 1, 12, 0)
        )

        export_measurement_tables_filtered_by_wargame_participation(
            self.source_store, self.destination_store, wg
        )

        with self.destination_store.session_scope():
            results = self.destination_store.session.query(
                self.destination_store.db_classes.State
            ).all()

            assert len(results) == 2

            times = [s.time for s in results]
            assert set(times) == set([datetime(2003, 10, 31, 12, 0), datetime(2003, 10, 31, 12, 6)])

            results = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(results) == 3

            starts = [s.start for s in results]
            assert set(starts) == set(
                [
                    None,
                    datetime(2003, 10, 31, 11, 0),
                    datetime(2003, 10, 31, 13, 0),
                ]
            )

    def test_export_filtered_by_serial_no_overlap(self):
        serial = self._create_serial(
            start_time=datetime(2000, 1, 1),
            end_time=datetime(2000, 2, 1),
            p1_start_time=datetime(2000, 1, 2),
            p1_end_time=datetime(2000, 1, 3),
        )

        export_measurement_tables_filtered_by_serial_participation(
            self.source_store, self.destination_store, serial
        )

        with self.destination_store.session_scope():
            for table in ["State", "Comment", "Contact", "Activation"]:
                results = self.destination_store.session.query(
                    getattr(self.destination_store.db_classes, table)
                ).all()

                assert len(results) == 0

    def test_export_filtered_by_serial_with_overlap(self):
        serial = self._create_serial(
            start_time=datetime(2003, 10, 31, 11, 0),
            end_time=datetime(2003, 11, 1, 12, 0),
            p1_start_time=datetime(2003, 10, 31, 11, 30),
            p1_end_time=datetime(2003, 10, 31, 14, 55),
        )

        export_measurement_tables_filtered_by_serial_participation(
            self.source_store, self.destination_store, serial
        )

        with self.destination_store.session_scope():
            # Check States
            states = self.destination_store.session.query(
                self.destination_store.db_classes.State
            ).all()

            assert len(states) == 2
            times = [s.time for s in states]
            assert set(times) == set([datetime(2003, 10, 31, 12, 0), datetime(2003, 10, 31, 12, 6)])

            # Check Activations
            activations = self.destination_store.session.query(
                self.destination_store.db_classes.Activation
            ).all()

            assert len(activations) == 1
            times = [s.start for s in activations]
            assert times == [datetime(2003, 10, 31, 13, 0)]

    def _create_wargame(self, start_time, end_time):
        with self.source_store.session_scope():
            priv_id = (
                self.source_store.session.query(self.source_store.db_classes.Privacy)
                .all()[0]
                .privacy_id
            )
            change_id = self.source_store.add_to_changes(
                "USER", datetime.utcnow(), "Creating test tasks/participants"
            ).change_id
            s1 = self.source_store.db_classes.Series(name="Test Series", privacy_id=priv_id)

            wg1 = self.source_store.db_classes.Wargame(
                name="Test Wargame",
                start=start_time,
                end=end_time,
                privacy_id=priv_id,
            )
            wg1.series = s1

            self.source_store.session.add_all([s1, wg1])

            plat1 = (
                self.source_store.session.query(self.source_store.db_classes.Platform)
                .filter(self.source_store.db_classes.Platform.name == "ADRI")
                .filter(self.source_store.db_classes.Platform.identifier == "123")
                .one()
            )

            wg1.add_participant(
                data_store=self.source_store, platform=plat1, privacy="Private", change_id=change_id
            )

        return wg1

    def _create_serial(self, start_time, end_time, p1_start_time, p1_end_time):
        with self.source_store.session_scope():
            priv_id = (
                self.source_store.session.query(self.source_store.db_classes.Privacy)
                .all()[0]
                .privacy_id
            )
            change_id = self.source_store.add_to_changes(
                "USER", datetime.utcnow(), "Creating test tasks/participants"
            ).change_id
            s1 = self.source_store.db_classes.Series(name="Test Series", privacy_id=priv_id)

            wg1 = self.source_store.db_classes.Wargame(
                name="Test Wargame",
                start=start_time,
                end=end_time,
                privacy_id=priv_id,
            )
            wg1.series = s1

            self.source_store.session.add_all([s1, wg1])

            plat1 = (
                self.source_store.session.query(self.source_store.db_classes.Platform)
                .filter(self.source_store.db_classes.Platform.name == "ADRI")
                .filter(self.source_store.db_classes.Platform.identifier == "123")
                .one()
            )

            p1 = wg1.add_participant(
                data_store=self.source_store, platform=plat1, privacy="Private", change_id=change_id
            )

            serial1 = self.source_store.db_classes.Serial(
                serial_number="Test Serial",
                exercise="Test Exercise",
                start=start_time,
                end=end_time,
                environment="Test Environment",
                privacy_id=priv_id,
            )
            serial1.wargame = wg1

            serial1.add_participant(
                data_store=self.source_store,
                wargame_participant=p1,
                start=p1_start_time,
                end=p1_end_time,
                force_type="Blue",
                privacy="Private",
                change_id=change_id,
            )

        return serial1
