import os

from importers.replay_importer import ReplayImporter
from pepys_admin.utils import sqlalchemy_obj_to_dict
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.test_utils import FakeDatafile

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")
DATA_PATH = os.path.join(dir_path, "..", "sample_data")
REP_TEST1_DATA_PATH = os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep")


def test_pending_extractions_generation():
    hf = HighlightedFile(DATA_FILE)
    hf.datafile = FakeDatafile()

    hf.importer_highlighting_levels["Test Importer"] = "database"

    lines = hf.lines()
    lines[0].record("Test Importer", "Test Field", "Test Value", "Test Units")
    lines[1].record("Test Importer", "Test Field 2", "Test Value")

    assert len(hf.datafile.pending_extracted_tokens) == 2

    assert hf.datafile.pending_extracted_tokens[0] == {
        "field": "Test Field",
        "importer": "Test Importer",
        "interpreted_value": "Test Value",
        "text": "951212 050000.000 MONDEO_44   @C   269.7   10.0      10",
        "text_location": "0-55",
    }

    assert hf.datafile.pending_extracted_tokens[1] == {
        "field": "Test Field 2",
        "importer": "Test Importer",
        "interpreted_value": "Test Value",
        "text": "// EVENT 951212 050300.000 BRAVO",
        "text_location": "56-88",
    }


def test_extraction_into_measurement_object_tokens_dict():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    hf = HighlightedFile(DATA_FILE)
    hf.datafile = ds.db_classes.Datafile()

    hf.importer_highlighting_levels["Test Importer"] = "database"

    lines = hf.lines()
    lines[0].record("Test Importer", "Test Field", "Test Value", "Test Units")
    lines[1].record("Test Importer", "Test Field 2", "Test Value")

    hf.datafile.current_measurement_object = "TEST"

    hf.datafile.flush_extracted_tokens()

    assert len(hf.datafile.measurement_object_to_tokens_list) == 1
    assert hf.datafile.measurement_object_to_tokens_list["TEST"] == [
        {
            "field": "Test Field",
            "importer": "Test Importer",
            "interpreted_value": "Test Value",
            "text": "951212 050000.000 MONDEO_44   @C   269.7   10.0      10",
            "text_location": "0-55",
        },
        {
            "field": "Test Field 2",
            "importer": "Test Importer",
            "interpreted_value": "Test Value",
            "text": "// EVENT 951212 050300.000 BRAVO",
            "text_location": "56-88",
        },
    ]


def test_recording_to_database_single_file():
    ds = DataStore("", "", "", 0, "extraction.db", db_type="sqlite")
    ds.initialise()

    processor = FileProcessor(archive=False)

    rep_importer = ReplayImporter()
    rep_importer.set_highlighting_level("database")

    processor.register_importer(rep_importer)

    processor.process(REP_TEST1_DATA_PATH, ds, True)

    with ds.session_scope():
        all_results = ds.session.query(ds.db_classes.Extraction).all()

        assert len(all_results) == 56

        state_entry = ds.session.query(ds.db_classes.State).first()

        extractions_for_state = (
            ds.session.query(ds.db_classes.Extraction)
            .filter(ds.db_classes.Extraction.entry_id == state_entry.state_id)
            .all()
        )

        assert len(extractions_for_state) == 7

        extractions = [
            sqlalchemy_obj_to_dict(item, remove_id=True) for item in extractions_for_state
        ]

        entry_id = state_entry.state_id
        datafile_id = state_entry.source_id

        assert extractions == [
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "timestamp",
                "importer": "Replay File Format Importer",
                "interpreted_value": "2010-01-12 11:58:00",
                "text": "100112 115800",
                "text_location": "240-253",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "vessel name",
                "importer": "Replay File Format Importer",
                "interpreted_value": "SUBJECT",
                "text": "SUBJECT",
                "text_location": "254-261",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "latitude",
                "importer": "Replay File Format Importer",
                "interpreted_value": "None, 60.395",
                "text": "60 23 40.25 N",
                "text_location": "265-278",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "longitude",
                "importer": "Replay File Format Importer",
                "interpreted_value": "0.024, 60.395",
                "text": "000 01 25.86 E",
                "text_location": "279-293",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "heading",
                "importer": "Replay File Format Importer",
                "interpreted_value": "109.08 degree",
                "text": "109.08",
                "text_location": "294-300",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "speed",
                "importer": "Replay File Format Importer",
                "interpreted_value": "6.0 knot",
                "text": "6.00",
                "text_location": "302-306",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "depth",
                "importer": "Replay File Format Importer",
                "interpreted_value": "0.0 meter",
                "text": "0.00",
                "text_location": "308-312",
            },
        ]
