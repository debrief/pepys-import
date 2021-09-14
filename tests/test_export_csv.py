import csv
import os
import tempfile
from pathlib import Path

import pytest

from pepys_import.core.store.data_store import DataStore


def read_csv(filename):
    with open(filename, newline="") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data


def test_convert_ids_to_objects():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()
    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    results = ds.convert_ids_to_objects(ids, ds.db_classes.PlatformType)
    assert results is not None
    assert len(results) == 8
    assert "Naval -" in str(results[0])


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
    # Generate the file and populate the data within it
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
