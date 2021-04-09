from datetime import datetime

from pepys_import.core.store.data_store import DataStore


def create_example_tasks(ds, create_participants=False):
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with ds.session_scope():
        priv_id = ds.session.query(ds.db_classes.Privacy).all()[0].privacy_id

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

        plat1 = ds.session.query(ds.db_classes.Platform).all()[0]
        plat2 = ds.session.query(ds.db_classes.Platform).all()[1]
        plat3 = ds.session.query(ds.db_classes.Platform).all()[2]

        if create_participants:
            wg1.add_participant(data_store=ds, platform=plat1, privacy="Private")
            wg1.add_participant(data_store=ds, platform=plat2, privacy="Private")
            wg1.add_participant(data_store=ds, platform=plat3, privacy="Private")

            serial1.add_participant(
                data_store=ds,
                wargame_participant=wg1.participants[0],
                start=datetime(2020, 2, 3, 8, 0, 0),
                end=datetime(2020, 2, 3, 10, 0, 0),
                force="Blue",
                privacy="Private",
            )

            serial1.add_participant(
                data_store=ds,
                wargame_participant=wg1.participants[1],
                start=datetime(2020, 2, 3, 8, 0, 0),
                end=datetime(2020, 2, 3, 9, 30, 0),
                force="Red",
                privacy="Private",
            )

            serial2.add_participant(
                data_store=ds,
                wargame_participant=wg1.participants[2],
                start=datetime(2020, 2, 6, 11, 0, 0),
                end=datetime(2020, 2, 7, 11, 0, 0),
                force="Blue",
                privacy="Private",
            )


def test_create_tasks():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds)

    with ds.session_scope():
        all_series = ds.session.query(ds.db_classes.Series).all()
        all_wargames = ds.session.query(ds.db_classes.Wargame).all()
        all_serials = ds.session.query(ds.db_classes.Serial).all()

        assert len(all_series) == 2
        assert len(all_wargames) == 3
        assert len(all_serials) == 3

        jw_series = (
            ds.session.query(ds.db_classes.Series)
            .filter(ds.db_classes.Series.name == "Joint Warrior")
            .one()
        )
        other_series = (
            ds.session.query(ds.db_classes.Series)
            .filter(ds.db_classes.Series.name == "Another Top-Level Series")
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


def test_create_participants():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    all_wgps = ds.session.query(ds.db_classes.WargameParticipant).all()
    all_sps = ds.session.query(ds.db_classes.SerialParticipant).all()

    assert len(all_wgps) == 3
    assert len(all_sps) == 3

    jw_wargame = (
        ds.session.query(ds.db_classes.Wargame)
        .filter(ds.db_classes.Wargame.name == "Joint Warrior 20/02")
        .one()
    )

    assert len(jw_wargame.participants) == 3
    platform_names = [participant.platform_name for participant in jw_wargame.participants]
    assert "ADRI" in platform_names
    assert "JEAN" in platform_names
    assert "NARV" in platform_names

    serial1 = (
        ds.session.query(ds.db_classes.Serial)
        .filter(ds.db_classes.Serial.serial_number == "J05020")
        .one()
    )
    assert len(serial1.participants) == 2
    platform_names = [participant.platform_name for participant in serial1.participants]
    assert "ADRI" in platform_names
    assert "JEAN" in platform_names


def test_delete_task_deletes_children_and_participants():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    with ds.session_scope():
        wargame = (
            ds.session.query(ds.db_classes.Wargame)
            .filter(ds.db_classes.Wargame.name == "Joint Warrior 20/02")
            .one()
        )

        ds.session.delete(wargame)

    with ds.session_scope():
        all_wargames = ds.session.query(ds.db_classes.Wargame).all()
        all_serials = ds.session.query(ds.db_classes.Serial).all()

        assert len(all_wargames) == 2
        assert len(all_serials) == 0

        # Should still have parent
        parent_series = (
            ds.session.query(ds.db_classes.Series)
            .filter(ds.db_classes.Series.name == "Joint Warrior")
            .all()
        )
        assert len(parent_series) == 1

        # The only participants were those under one of the deleted tasks, so they should be deleted too
        all_wgps = ds.session.query(ds.db_classes.WargameParticipant).all()
        assert len(all_wgps) == 0

        all_sps = ds.session.query(ds.db_classes.SerialParticipant).all()
        assert len(all_sps) == 0

        # But the platforms the participants reference shouldn't be deleted
        all_platforms = ds.session.query(ds.db_classes.Platform).all()
        assert len(all_platforms) == 4


def test_removing_serial_participant_deletes_it():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    with ds.session_scope():
        serial = (
            ds.session.query(ds.db_classes.Serial)
            .filter(ds.db_classes.Serial.serial_number == "J05020")
            .one()
        )

        serial.participants.remove(serial.participants[0])

    with ds.session_scope():
        serial = (
            ds.session.query(ds.db_classes.Serial)
            .filter(ds.db_classes.Serial.serial_number == "J05020")
            .one()
        )

        assert len(serial.participants) == 1

        # Check it deletes the SerialParticipant entry
        all_sps = ds.session.query(ds.db_classes.SerialParticipant).all()
        assert len(all_sps) == 2

        # Check it doesn't delete the wargame participant associated with it
        all_wgps = ds.session.query(ds.db_classes.WargameParticipant).all()
        assert len(all_wgps) == 3


def test_removing_wargame_participant_deletes_it_and_serial_participants():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    create_example_tasks(ds, create_participants=True)

    with ds.session_scope():
        wargame = (
            ds.session.query(ds.db_classes.Wargame)
            .filter(ds.db_classes.Wargame.name == "Joint Warrior 20/02")
            .one()
        )

        wargame.participants.remove(wargame.participants[0])

    with ds.session_scope():
        serial = (
            ds.session.query(ds.db_classes.Serial)
            .filter(ds.db_classes.Serial.serial_number == "J05020")
            .one()
        )

        assert len(serial.participants) == 1

        # Check it deletes the WargameParticipant entry
        all_wgps = ds.session.query(ds.db_classes.WargameParticipant).all()
        assert len(all_wgps) == 2

        # Check it also deletes the SerialParticipant entry
        all_sps = ds.session.query(ds.db_classes.SerialParticipant).all()
        assert len(all_sps) == 2
