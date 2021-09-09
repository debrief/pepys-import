import os
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from pepys_import.core.store.data_store import DataStore


def test_convert_ids_to_objects():
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    with ds.session_scope():
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]
        print(ids)
    results = ds.convert_ids_to_objects(ids, ds.db_classes.PlatformType)
    assert results is not None
    assert results.count() == 8
    assert results[0].name == "Naval - destroyer"


def test_convert_ids_to_objects_no_ids():
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        # Call the function
        results = ds.convert_ids_to_objects(None, ds.db_classes.PlatformType)
    output = temp_output.getvalue()
    assert "Error converting ID's to objects: No primary key IDs provided." in output
    assert results is None


def test_export_objects_to_csv_file_created():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    with ds.session_scope():
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    # Call the function
    ds.export_objects_to_csv(
        ds.db_classes.PlatformType,
        ids,
        ["platform_type_id", "name", "default_data_interval_secs"],
        fileName,
    )

    # Check that the file has been made
    result = Path(fileName)
    assert result.exists()

    # Remove the file that was made
    os.remove(fileName)


def test_export_object_to_csv_no_filename():
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    with ds.session_scope():
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        # Call the function
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType,
            ids,
            ["platform_type_id", "name", "default_data_interval_secs"],
            None,
        )
    output = temp_output.getvalue()
    assert "Input Error: No output filepath provided." in output


def test_export_object_to_csv_no_id_list():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        # Call the function
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType,
            None,
            ["platform_type_id", "name", "default_data_interval_secs"],
            fileName,
        )
    output = temp_output.getvalue()
    assert "Error retrieving objects - No objects found from list of chosen ids." in output


def test_export_object_to_csv_incorrect_header():
    fileName = str(tempfile.gettempdir()) + "/output.csv"
    ds = DataStore("", "", "", 0, "export_test.db", db_type="sqlite")

    with ds.session_scope():
        entries = ds.session.query(ds.db_classes.PlatformType).all()[:8]
        ids = [entry.platform_type_id for entry in entries]

    temp_output = StringIO()
    with redirect_stdout(temp_output):
        # Call the function
        ds.export_objects_to_csv(
            ds.db_classes.PlatformType, ids, ["Wrong_column", "error", "doesn't_exist"], fileName
        )
    output = temp_output.getvalue()
    assert "Attribute Error: Given column header:" in output
