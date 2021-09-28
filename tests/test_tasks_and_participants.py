import unittest
from datetime import datetime

import pytest
from testing.postgresql import Postgresql

from pepys_import.core.store.data_store import DataStore


def create_example_tasks(ds, create_participants=False):
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with ds.session_scope():
        priv_id = ds.session.query(ds.db_classes.Privacy).all()[0].privacy_id
        change_id = ds.add_to_changes(
            "USER", datetime.utcnow(), "Creating test tasks/participants"
        ).change_id

        s1 = ds.db_classes.Series(name="Joint Warrior", privacy_id=priv_id)
        s2 = ds.db_classes.Series(name="Another Top-Level Series", privacy_id=priv_id)

        wg1 = ds.db_classes.Wargame(
            name="Joint Warrior 20/02",
            start=datetime(2020, 2, 1, 0, 0, 0),
            end=datetime(2020, 2, 28, 0, 0, 0),
            privacy_id=priv_id,
        )
        wg1.series = s1

        wg2 = ds.db_classes.Wargame(
            name="An Wargame",
            start=datetime(2020, 2, 1, 0, 0, 0),
            end=datetime(2020, 2, 28, 0, 0, 0),
            privacy_id=priv_id,
        )
        wg2.series = s2

        wg3 = ds.db_classes.Wargame(
            name="Another Wargame",
            start=datetime(2020, 2, 1, 0, 0, 0),
            end=datetime(2020, 2, 28, 0, 0, 0),
            privacy_id=priv_id,
        )
        wg3.series = s2

        serial1 = ds.db_classes.Serial(
            serial_number="J05020",
            exercise="NAVCOMEX",
            start=datetime(2020, 2, 3, 7, 0, 0),
            end=datetime(2020, 2, 4, 12, 0, 0),
            environment="Test Environment",
            privacy_id=priv_id,
        )
        serial1.wargame = wg1

        serial2 = ds.db_classes.Serial(
            serial_number="J05084",
            exercise="ADEX 324",
            start=datetime(2020, 2, 6, 9, 0, 0),
            end=datetime(2020, 2, 8, 14, 0, 0),
            environment="Test Environment",
            privacy_id=priv_id,
        )
        serial2.wargame = wg1

        serial3 = ds.db_classes.Serial(
            serial_number="J05110",
            exercise="CASEX E3",
            start=datetime(2020, 2, 23, 9, 0, 0),
            end=datetime(2020, 2, 25, 15, 0, 0),
            environment="Test Environment",
            privacy_id=priv_id,
        )
        serial3.wargame = wg1

        ds.session.add_all([s1, s2, wg1, wg2, wg3, serial1, serial2, serial3])

        plat1 = (
            ds.session.query(ds.db_classes.Platform)
            .filter(ds.db_classes.Platform.name == "ADRI")
            .one()
        )
        plat2 = (
            ds.session.query(ds.db_classes.Platform)
            .filter(ds.db_classes.Platform.name == "JEAN")
            .one()
        )
        plat3 = (
            ds.session.query(ds.db_classes.Platform)
            .filter(ds.db_classes.Platform.name == "NARV")
            .one()
        )

        if create_participants:
            p1 = wg1.add_participant(
                data_store=ds, platform=plat1, privacy="Private", change_id=change_id
            )
            p2 = wg1.add_participant(
                data_store=ds, platform=plat2, privacy="Private", change_id=change_id
            )
            p3 = wg1.add_participant(
                data_store=ds, platform=plat3, privacy="Private", change_id=change_id
            )

            serial1.add_participant(
                data_store=ds,
                wargame_participant=p1,
                start=datetime(2020, 2, 3, 8, 0, 0),
                end=datetime(2020, 2, 3, 10, 0, 0),
                force_type="Blue",
                privacy="Private",
                change_id=change_id,
            )

            serial1.add_participant(
                data_store=ds,
                wargame_participant=p2,
                start=datetime(2020, 2, 3, 8, 0, 0),
                end=datetime(2020, 2, 3, 9, 30, 0),
                force_type="Red",
                privacy="Private",
                change_id=change_id,
            )

            serial2.add_participant(
                data_store=ds,
                wargame_participant=p3,
                start=datetime(2020, 2, 6, 11, 0, 0),
                end=datetime(2020, 2, 7, 11, 0, 0),
                force_type="Blue",
                privacy="Private",
                change_id=change_id,
            )


class TestTasksAndParticipants_SQLite(unittest.TestCase):
    def setUp(self):
        self.store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")

    def test_create_tasks(self):
        create_example_tasks(self.store)

        with self.store.session_scope():
            all_series = self.store.session.query(self.store.db_classes.Series).all()
            all_wargames = self.store.session.query(self.store.db_classes.Wargame).all()
            all_serials = self.store.session.query(self.store.db_classes.Serial).all()

            assert len(all_series) == 2
            assert len(all_wargames) == 3
            assert len(all_serials) == 3

            jw_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Joint Warrior")
                .one()
            )
            other_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Another Top-Level Series")
                .one()
            )

            assert len(jw_series.child_wargames) == 1
            assert len(other_series.child_wargames) == 2

            jw_wargame = jw_series.child_wargames[0]

            assert jw_wargame.name == "Joint Warrior 20/02"
            assert len(jw_wargame.child_serials) == 3
            assert jw_wargame.series == jw_series
            assert jw_wargame.series_name == "Joint Warrior"

            serial_numbers = [serial.serial_number for serial in jw_wargame.child_serials]
            assert "J05020" in serial_numbers
            assert "J05084" in serial_numbers
            assert "J05110" in serial_numbers

            serial_exercises = [serial.exercise for serial in jw_wargame.child_serials]
            assert "NAVCOMEX" in serial_exercises
            assert "ADEX 324" in serial_exercises
            assert "CASEX E3" in serial_exercises

    def test_create_participants(self):
        create_example_tasks(self.store, create_participants=True)

        all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
        all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()

        assert len(all_wgps) == 3
        assert len(all_sps) == 3

        jw_wargame = (
            self.store.session.query(self.store.db_classes.Wargame)
            .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
            .one()
        )

        assert len(jw_wargame.participants) == 3
        platform_names = [participant.platform_name for participant in jw_wargame.participants]
        assert "ADRI" in platform_names
        assert "JEAN" in platform_names
        assert "NARV" in platform_names

        serial1 = (
            self.store.session.query(self.store.db_classes.Serial)
            .filter(self.store.db_classes.Serial.serial_number == "J05020")
            .one()
        )
        assert len(serial1.participants) == 2
        platform_names = [participant.platform_name for participant in serial1.participants]
        assert "ADRI" in platform_names
        assert "JEAN" in platform_names

        force_types = [participant.force_type_name for participant in serial1.participants]
        assert "Red" in force_types
        assert "Blue" in force_types

    def test_delete_task_deletes_children_and_participants(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            wargame = (
                self.store.session.query(self.store.db_classes.Wargame)
                .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
                .one()
            )

            self.store.session.delete(wargame)

        with self.store.session_scope():
            all_wargames = self.store.session.query(self.store.db_classes.Wargame).all()
            all_serials = self.store.session.query(self.store.db_classes.Serial).all()

            assert len(all_wargames) == 2
            assert len(all_serials) == 0

            # Should still have parent
            parent_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Joint Warrior")
                .all()
            )
            assert len(parent_series) == 1

            # The only participants were those under one of the deleted tasks, so they should be deleted too
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 0

            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 0

            # But the platforms the participants reference shouldn't be deleted
            all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(all_platforms) == 4

    def test_removing_serial_participant_deletes_it(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            serial.participants.remove(serial.participants[0])

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            assert len(serial.participants) == 1

            # Check it deletes the SerialParticipant entry
            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 2

            # Check it doesn't delete the wargame participant associated with it
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 3

    def test_removing_wargame_participant_deletes_it_and_serial_participants(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            wargame = (
                self.store.session.query(self.store.db_classes.Wargame)
                .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
                .one()
            )
            narv_participant = [
                participant
                for participant in wargame.participants
                if participant.platform_name == "ADRI"
            ][0]
            wargame.participants.remove(narv_participant)

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            assert len(serial.participants) == 1

            # Check it deletes the WargameParticipant entry
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 2

            # Check it also deletes the SerialParticipant entry
            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 2


@pytest.mark.postgres
class TestTasksAndParticipants_Postgres(unittest.TestCase):
    def setUp(self):
        self.postgres = None

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

        self.store = DataStore(
            db_name="test",
            db_host="localhost",
            db_username="postgres",
            db_password="postgres",
            db_port=55527,
            db_type="postgres",
        )

    def tearDown(self):
        try:
            self.postgres.stop()
        except AttributeError:
            return

    def test_create_tasks(self):
        create_example_tasks(self.store)

        with self.store.session_scope():
            all_series = self.store.session.query(self.store.db_classes.Series).all()
            all_wargames = self.store.session.query(self.store.db_classes.Wargame).all()
            all_serials = self.store.session.query(self.store.db_classes.Serial).all()

            assert len(all_series) == 2
            assert len(all_wargames) == 3
            assert len(all_serials) == 3

            jw_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Joint Warrior")
                .one()
            )
            other_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Another Top-Level Series")
                .one()
            )

            assert len(jw_series.child_wargames) == 1
            assert len(other_series.child_wargames) == 2

            jw_wargame = jw_series.child_wargames[0]

            assert jw_wargame.name == "Joint Warrior 20/02"
            assert len(jw_wargame.child_serials) == 3
            assert jw_wargame.series == jw_series
            assert jw_wargame.series_name == "Joint Warrior"

            serial_numbers = [serial.serial_number for serial in jw_wargame.child_serials]
            assert "J05020" in serial_numbers
            assert "J05084" in serial_numbers
            assert "J05110" in serial_numbers

            serial_exercises = [serial.exercise for serial in jw_wargame.child_serials]
            assert "NAVCOMEX" in serial_exercises
            assert "ADEX 324" in serial_exercises
            assert "CASEX E3" in serial_exercises

    def test_create_participants(self):
        create_example_tasks(self.store, create_participants=True)

        all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
        all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()

        assert len(all_wgps) == 3
        assert len(all_sps) == 3

        jw_wargame = (
            self.store.session.query(self.store.db_classes.Wargame)
            .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
            .one()
        )

        assert len(jw_wargame.participants) == 3
        platform_names = [participant.platform_name for participant in jw_wargame.participants]
        assert "ADRI" in platform_names
        assert "JEAN" in platform_names
        assert "NARV" in platform_names

        serial1 = (
            self.store.session.query(self.store.db_classes.Serial)
            .filter(self.store.db_classes.Serial.serial_number == "J05020")
            .one()
        )
        assert len(serial1.participants) == 2
        platform_names = [participant.platform_name for participant in serial1.participants]
        assert "ADRI" in platform_names
        assert "JEAN" in platform_names

        force_types = [participant.force_type_name for participant in serial1.participants]
        assert "Red" in force_types
        assert "Blue" in force_types

    def test_delete_task_deletes_children_and_participants(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            wargame = (
                self.store.session.query(self.store.db_classes.Wargame)
                .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
                .one()
            )

            self.store.session.delete(wargame)

        with self.store.session_scope():
            all_wargames = self.store.session.query(self.store.db_classes.Wargame).all()
            all_serials = self.store.session.query(self.store.db_classes.Serial).all()

            assert len(all_wargames) == 2
            assert len(all_serials) == 0

            # Should still have parent
            parent_series = (
                self.store.session.query(self.store.db_classes.Series)
                .filter(self.store.db_classes.Series.name == "Joint Warrior")
                .all()
            )
            assert len(parent_series) == 1

            # The only participants were those under one of the deleted tasks, so they should be deleted too
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 0

            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 0

            # But the platforms the participants reference shouldn't be deleted
            all_platforms = self.store.session.query(self.store.db_classes.Platform).all()
            assert len(all_platforms) == 4

    def test_removing_serial_participant_deletes_it(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            serial.participants.remove(serial.participants[0])

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            assert len(serial.participants) == 1

            # Check it deletes the SerialParticipant entry
            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 2

            # Check it doesn't delete the wargame participant associated with it
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 3

    def test_removing_wargame_participant_deletes_it_and_serial_participants(self):
        create_example_tasks(self.store, create_participants=True)

        with self.store.session_scope():
            wargame = (
                self.store.session.query(self.store.db_classes.Wargame)
                .filter(self.store.db_classes.Wargame.name == "Joint Warrior 20/02")
                .one()
            )
            narv_participant = [
                participant
                for participant in wargame.participants
                if participant.platform_name == "ADRI"
            ][0]
            wargame.participants.remove(narv_participant)

        with self.store.session_scope():
            serial = (
                self.store.session.query(self.store.db_classes.Serial)
                .filter(self.store.db_classes.Serial.serial_number == "J05020")
                .one()
            )

            assert len(serial.participants) == 1

            # Check it deletes the WargameParticipant entry
            all_wgps = self.store.session.query(self.store.db_classes.WargameParticipant).all()
            assert len(all_wgps) == 2

            # Check it also deletes the SerialParticipant entry
            all_sps = self.store.session.query(self.store.db_classes.SerialParticipant).all()
            assert len(all_sps) == 2
