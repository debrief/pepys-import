import csv
import os
import tempfile
from pathlib import Path

import pytest

from pepys_import.core.store.data_store import DataStore


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


def test_export_object_to_csv_correct_file_contents():
    # Generate the file and populate the data within it
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    columns = ["platform_type_id", "name", "default_data_interval_secs"]
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    with ds.session_scope():
        ds.populate_reference()
        ds.populate_metadata()
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    actual_entries = []
    for entry in entries:
        e = []
        for column in columns:
            attribute = str(getattr(entry, column))
            e.append(attribute)
        actual_entries.append(e)
    actual_entries.sort()

    ds.export_objects_to_csv(
        ds.db_classes.PlatformType,
        ids,
        columns,
        fileName,
    )

    # Read the first line of the file and check that it matches what we expect
    with open(fileName, "r", newline="") as file:
        csv_reader = csv.reader(file, delimiter=",")
        line = 0
        for row in csv_reader:
            if line == 0:
                # Header will appear on row one
                header_line = row
                line += 1

                assert header_line == ["platform_type_id", "name", "default_data_interval_secs"]
            else:
                # Data rows will appear on other rows - entires array is one shorter as no header so -1 from line
                current_entry_line = actual_entries[line - 1]
                test_cell_1 = actual_entries[line - 1][0]
                test_cell_2 = actual_entries[line - 1][1]
                test_cell_3 = actual_entries[line - 1][2]

                actual_entry_line = row
                actual_test_cell_1 = row[0]
                actual_test_cell_2 = row[1]
                actual_test_cell_3 = row[2]

                assert current_entry_line == actual_entry_line
                assert test_cell_1 == actual_test_cell_1
                assert test_cell_2 == actual_test_cell_2
                assert test_cell_3 == actual_test_cell_3
                line += 1
    # Remove the file that was made
    os.remove(fileName)
