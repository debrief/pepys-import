from datetime import datetime

import pytest

from pepys_import.core.store.data_store import DataStore


@pytest.mark.parametrize(
    "func_name, class_name",
    [
        ("add_to_comment_types", "CommentType"),
        ("add_to_platform_types", "PlatformType"),
        ("add_to_nationalities", "Nationality"),
        ("add_to_privacies", "Privacy"),
        ("add_to_datafile_types", "DatafileType"),
        ("add_to_sensor_types", "SensorType"),
        ("add_to_geometry_types", "GeometryType"),
    ],
)
def test_adding_duplicate_reference_data(func_name, class_name):
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        add_func = getattr(store, func_name)

        if "privacies" in func_name:
            result = add_func("TestName", level=0, change_id=change_id)
        else:
            result = add_func("TestName", change_id=change_id)

        results = store.session.query(getattr(store.db_classes, class_name)).all()

        # Should be one entry now
        assert len(results) == 1

    with store.session_scope():
        change_id = store.add_to_changes("TEST", datetime.utcnow(), "TEST").change_id
        add_func = getattr(store, func_name)

        if "privacies" in func_name:
            result = add_func("TESTNAME", level=0, change_id=change_id)
        else:
            result = add_func("TESTNAME", change_id=change_id)

        results = store.session.query(getattr(store.db_classes, class_name)).all()

        # Should be one entry now
        assert len(results) == 1

        assert result.name == "TestName"


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


def test_adding_duplicate_platform_with_case_difference():
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
        plat = store.add_to_platforms(
            "TESTPLATFORM",
            "TestIdentifier",
            "United Kingdom",
            "PLATFORM-TYPE-1",
            "Public",
            change_id=change_id,
        )

        results = store.session.query(store.db_classes.Platform).all()

        # Should still be one Platform
        assert len(results) == 1

        # Platform should have original case
        assert plat.name == "TestPlatform"


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


def test_adding_duplicate_sensor_with_case_difference():
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
        sensor = store.add_to_sensors(
            name="TESTSENSOR",
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

        # Should have original case
        assert sensor.name == "TestSensor"


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


def test_adding_duplicate_synonym_with_case_difference():
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
        syn = store.add_to_synonyms("Platforms", "TESTSYNONYM", platform_id, change_id=change_id)

        results = store.session.query(store.db_classes.Synonym).all()

        # Should still be one Synonym
        assert len(results) == 1

        assert syn.synonym == "TestSynonym"
