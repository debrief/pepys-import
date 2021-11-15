import csv
import os
import tempfile
from pathlib import Path

import pytest

from importers.gpx_importer import GPXImporter
from importers.nisida_importer import NisidaImporter
from importers.replay_importer import ReplayImporter
from pepys_admin.maintenance.column_data import create_column_data
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name

REP_FILE = os.path.join(os.path.dirname(__file__), "sample_data/track_files/rep_data/uk_track.rep")
GPX_FILE = os.path.join(os.path.dirname(__file__), "sample_data/track_files/gpx/gpx_1_0.gpx")
NISIDA_FILE = os.path.join(
    os.path.dirname(__file__), "sample_data/track_files/nisida/nisida_example.txt"
)


def read_csv(filename):
    with open(filename, newline="") as file:
        reader = csv.DictReader(file)
        data = list(reader)

    return data


def test_convert_ids_to_objects():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = (
            ds.session.query(ds.db_classes.PlatformType)
            .order_by(ds.db_classes.PlatformType.name)
            .all()[:8]
        )
        ids = [entry.platform_type_id for entry in entries]

    results = ds.convert_ids_to_objects(ids, ds.db_classes.PlatformType)
    assert results is not None
    assert len(results) == 8
    names = [r.name for r in results]

    assert set(names) == set(
        [
            "Attack Craft",
            "Civilian - uncrewed air vehicle",
            "Civilian - uncrewed surface vehicle",
            "Civilian - uncrewed underwater vehicle",
            "Commercial aircraft",
            "Fishing Vessel",
            "High Speed Craft",
            "Law Enforcement",
        ]
    )


def test_convert_ids_to_objects_no_ids():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with pytest.raises(Exception, match="No ids provided"):
        ds.convert_ids_to_objects(None, ds.db_classes.PlatformType)


def test_export_objects_to_csv_file_created():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    # Call the function
    ds.export_objects_to_csv(
        ds.db_classes.PlatformType,
        ids,
        ["platform_type_id", "name", "default_data_interval_secs"],
        fileName,
    )

    # Check that the file has been created
    result = Path(fileName)
    assert result.exists()

    # Remove the file that was created
    os.remove(fileName)


def test_export_object_to_csv_no_filename():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    with pytest.raises(Exception, match="Output filename must be provided"):
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType,
            ids,
            ["platform_type_id", "name", "default_data_interval_secs"],
            "",
        )


def test_export_object_to_csv_no_id_list():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

    with pytest.raises(Exception, match="Cannot export CSV: no entries selected"):
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType,
            [],
            ["platform_type_id", "name", "default_data_interval_secs"],
            fileName,
        )


def test_export_object_to_csv_incorrect_header():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    with pytest.raises(Exception, match="does not exist in database object"):
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType, ids, ["Wrong_column", "error", "doesn't_exist"], fileName
        )


def test_export_platform_type():
    filename = str(tempfile.gettempdir()) + "/output.csv"
    columns = ["platform_type_id", "name", "default_data_interval_secs"]
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    ds.export_objects_to_csv(
        ds.db_classes.PlatformType,
        ids,
        columns,
        filename,
    )

    objects = ds.convert_ids_to_objects(ids, ds.db_classes.PlatformType)

    export_contents = read_csv(filename)

    assert set(export_contents[0].keys()) == set(columns)

    for i in range(1, len(objects)):
        assert export_contents[i]["name"] == objects[i].name
        assert export_contents[i]["default_data_interval_secs"] == str(
            objects[i].default_data_interval_secs
        )
        assert export_contents[i]["platform_type_id"] == str(objects[i].platform_type_id)

    # Remove the file that was made
    os.remove(filename)


def test_export_state():
    filename = str(tempfile.gettempdir()) + "/output.csv"
    columns = [
        "state_id",
        "time",
        "location",
        "elevation",
        "heading",
        "course",
        "speed",
        "remarks",
        "created_date",
        "platform_name",
        "privacy_name",
        "sensor_name",
        "source_reference",
    ]
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()

        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())
        processor.register_importer(GPXImporter())

        processor.process(
            REP_FILE,
            ds,
            False,
        )
        processor.process(
            GPX_FILE,
            ds,
            False,
        )

    with ds.session_scope():
        entries = ds.session.query(ds.db_classes.State).all()
        ids = [entry.state_id for entry in entries]

    ds.export_objects_to_csv(
        ds.db_classes.State,
        ids,
        columns,
        filename,
    )

    objects = ds.convert_ids_to_objects(ids, ds.db_classes.State)

    export_contents = read_csv(filename)

    expected_cols = [
        "state_id",
        "time",
        "location_lat (decimal degrees)",
        "location_lon (decimal degrees)",
        "elevation (meter)",
        "heading (degree)",
        "course (degree)",
        "speed (meter / second)",
        "remarks",
        "created_date",
        "platform_name",
        "privacy_name",
        "sensor_name",
        "source_reference",
    ]
    assert set(export_contents[0].keys()) == set(expected_cols)

    for i in range(1, len(objects)):
        assert export_contents[i]["state_id"] == str(objects[i].state_id)
        assert export_contents[i]["time"] == str(objects[i].time)
        if objects[i].heading is not None:
            assert export_contents[i]["heading (degree)"] == str(objects[i].heading.magnitude)
        else:
            assert export_contents[i]["heading (degree)"] == ""
        assert export_contents[i]["platform_name"] == str(objects[i].platform_name)
        assert export_contents[i]["location_lat (decimal degrees)"] == str(
            objects[i].location.latitude
        )
        assert export_contents[i]["location_lon (decimal degrees)"] == str(
            objects[i].location.longitude
        )

    # Remove the file that was made
    os.remove(filename)


def get_list_of_all_tables(data_store):
    metadata_tables = [
        "Platforms",
        "Sensors",
        "Datafiles",
        "Series",
        "Wargames",
        "Serials",
        "WargameParticipants",
        "SerialParticipants",
        "ConfigOptions",
    ]
    measurement_tables = sorted(
        [mc.__tablename__ for mc in data_store.meta_classes[TableTypes.MEASUREMENT]]
    )
    reference_tables = sorted(
        [mc.__tablename__ for mc in data_store.meta_classes[TableTypes.REFERENCE]]
    )
    reference_tables.remove("HelpTexts")
    tables_list = metadata_tables + measurement_tables + reference_tables
    return tables_list


def test_exporting_all_tables():
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()
    with store.session_scope():
        store.populate_reference()
        store.populate_metadata()

        processor = FileProcessor(archive=False)
        processor.register_importer(ReplayImporter())
        processor.register_importer(GPXImporter())
        processor.register_importer(NisidaImporter())

        processor.process(
            REP_FILE,
            store,
            False,
        )
        processor.process(
            GPX_FILE,
            store,
            False,
        )
        processor.process(NISIDA_FILE)

    for table_name in get_list_of_all_tables(store):
        print(f"Running test for {table_name}")
        class_name = table_name_to_class_name(table_name)
        table_obj = getattr(store.db_classes, class_name)

        column_data = create_column_data(store, table_obj)

        all_column_names = []
        for _, data in column_data.items():
            if data["sqlalchemy_type"] == "relationship":
                continue
            all_column_names.append(data["system_name"])

        entries = store.session.query(table_obj).all()
        ids = [getattr(entry, get_primary_key_for_table(table_obj)) for entry in entries]

        filename = str(tempfile.gettempdir()) + "/output.csv"

        try:
            store.export_objects_to_csv(
                table_obj,
                ids,
                all_column_names,
                filename,
            )
        except Exception as e:
            if "Cannot export CSV: no entries selected" in str(e):
                continue
