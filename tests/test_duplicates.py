from datetime import datetime

from pepys_import.core.store.data_store import DataStore


def test_adding_duplicate_platform():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        store.populate_reference()
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

        store.add_to_platforms(
            "TestPlatform",
            "TestIdentifier",
            "United Kingdom",
            "PLATFORM-TYPE-1",
            "Public",
            change_id=change_id,
        )

        results = store.session.query(store.db_classes.Platform).all()

        # Should be one Platform now
        assert len(results) == 1

    with store.session_scope():
        # Add platform with same details again
        store.add_to_platforms(
            "TestPlatform",
            "TestIdentifier",
            "United Kingdom",
            "PLATFORM-TYPE-1",
            "Public",
            change_id=change_id,
        )

        results = store.session.query(store.db_classes.Platform).all()

        # Should still be one Platform
        assert len(results) == 1


def test_adding_duplicate_sensor():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        store.populate_reference()
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

        # Add Platform for this Sensor to belong to
        platform_id = store.add_to_platforms(
            "TestPlatform",
            "TestIdentifier",
            "United Kingdom",
            "PLATFORM-TYPE-1",
            "Public",
            change_id=change_id,
        ).platform_id

        store.add_to_sensors(
            name="TestSensor",
            sensor_type="GPS",
            host_id=platform_id,
            host_name=None,
            host_nationality=None,
            host_identifier=None,
            privacy="Public",
            change_id=change_id,
        )

        results = store.session.query(store.db_classes.Sensor).all()

        # Should be one Sensor now
        assert len(results) == 1

    with store.session_scope():
        # Add Sensor with same details again
        store.add_to_sensors(
            name="TestSensor",
            sensor_type="GPS",
            host_id=platform_id,
            host_name=None,
            host_nationality=None,
            host_identifier=None,
            privacy="Public",
            change_id=change_id,
        )

        results = store.session.query(store.db_classes.Sensor).all()

        # Should still be one Sensor
        assert len(results) == 1


def test_adding_duplicate_datafile():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        store.populate_reference()
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

        store.add_to_datafiles(
            "Public", "DATAFILE-TYPE-1", file_size=500, file_hash="TestHash", change_id=change_id
        )

        results = store.session.query(store.db_classes.Datafile).all()

        # Should be one Datafile now
        assert len(results) == 1

    with store.session_scope():
        # Add Datafile with same details again
        store.add_to_datafiles(
            "Public", "DATAFILE-TYPE-1", file_size=500, file_hash="TestHash", change_id=change_id
        )

        results = store.session.query(store.db_classes.Datafile).all()

        # Should still be one Datafile
        assert len(results) == 1


def test_adding_duplicate_synonym():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        store.populate_reference()
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id

        # Add Platform for the Synonym to point to
        platform = store.add_to_platforms(
            "TestPlatform",
            "TestIdentifier",
            "United Kingdom",
            "PLATFORM-TYPE-1",
            "Public",
            change_id=change_id,
        )

        platform_id = platform.platform_id

        store.add_to_synonyms("Platforms", "TestSynonym", platform_id, change_id=change_id)

        results = store.session.query(store.db_classes.Synonym).all()

        # Should be one Synonym now
        assert len(results) == 1

    with store.session_scope():
        # Add Synonym again
        store.add_to_synonyms("Platforms", "TestSynonym", platform_id, change_id=change_id)

        results = store.session.query(store.db_classes.Synonym).all()

        # Should still be one Synonym
        assert len(results) == 1
