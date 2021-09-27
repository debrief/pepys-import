import os
from unittest.mock import patch

from sqlalchemy import func

from importers.gpx_importer import GPXImporter
from importers.replay_comment_importer import ReplayCommentImporter
from importers.replay_contact_importer import ReplayContactImporter
from importers.replay_importer import ReplayImporter
from pepys_admin.utils import sqlalchemy_obj_to_dict
from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.level import HighlightLevel
from pepys_import.file.highlighter.support.test_utils import FakeDatafile

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)
DATA_FILE = os.path.join(dir_path, "sample_files/file.txt")
DATA_PATH = os.path.join(dir_path, "..", "sample_data")
REP_TEST1_PATH = os.path.join(DATA_PATH, "track_files", "rep_data", "rep_test1.rep")
UK_TRACK_PATH = os.path.join(DATA_PATH, "track_files", "rep_data", "uk_track.rep")
GPX_PATH = os.path.join(DATA_PATH, "track_files", "gpx", "gpx_1_0.gpx")
REP_FOLDER_PATH = os.path.join(DATA_PATH, "track_files", "rep_data")


def test_pending_extractions_generation():
    hf = HighlightedFile(DATA_FILE)
    hf.datafile = FakeDatafile()

    hf.importer_highlighting_levels["Test Importer"] = HighlightLevel.DATABASE

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

    hf.importer_highlighting_levels["Test Importer"] = HighlightLevel.DATABASE

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
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    processor = FileProcessor(archive=False)

    rep_importer = ReplayImporter()
    rep_importer.set_highlighting_level(HighlightLevel.DATABASE)

    processor.register_importer(rep_importer)

    processor.process(REP_TEST1_PATH, ds, True)

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


@patch("pepys_import.core.store.common_db.prompt", return_value="2")
def test_recording_to_database_multiple_files_and_importers(mock):
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    processor = FileProcessor(archive=False)

    rep_importer = ReplayImporter()
    rep_importer.set_highlighting_level(HighlightLevel.DATABASE)

    rep_com_importer = ReplayCommentImporter()
    rep_com_importer.set_highlighting_level(HighlightLevel.DATABASE)

    rep_contact_importer = ReplayContactImporter()
    rep_contact_importer.set_highlighting_level(HighlightLevel.DATABASE)

    processor.register_importer(rep_importer)
    processor.register_importer(rep_com_importer)
    processor.register_importer(rep_contact_importer)

    processor.process(REP_FOLDER_PATH, ds, False)

    with ds.session_scope():
        all_results = ds.session.query(ds.db_classes.Extraction).all()

        assert len(all_results) == 5784

        grouped_by_datafile = (
            ds.session.query(
                ds.db_classes.Datafile.reference,
                func.count(ds.db_classes.Extraction.datafile_id),
            )
            .group_by(ds.db_classes.Extraction.datafile_id)
            .join(ds.db_classes.Datafile)
            .all()
        )

        assert set(grouped_by_datafile) == set(
            [
                ("sen_tracks.rep", 2296),
                ("rep_test1.rep", 119),
                ("sen_ssk_freq.dsf", 32),
                ("uk_track.rep", 2814),
                ("sen_frig_sensor.dsf", 523),
            ]
        )

        grouped_by_importer = (
            ds.session.query(
                ds.db_classes.Extraction.importer,
                func.count(ds.db_classes.Extraction.importer),
            )
            .group_by(ds.db_classes.Extraction.importer)
            .all()
        )

        assert set(grouped_by_importer) == set(
            [
                ("Replay Comment Importer", 22),
                ("Replay Contact Importer", 596),
                ("Replay File Format Importer", 5166),
            ]
        )


def test_recording_to_database_single_xml_file():
    ds = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    ds.initialise()

    processor = FileProcessor(archive=False)

    gpx_importer = GPXImporter()
    gpx_importer.set_highlighting_level(HighlightLevel.DATABASE)

    processor.register_importer(gpx_importer)

    processor.process(GPX_PATH, ds, True)

    with ds.session_scope():
        all_results = ds.session.query(ds.db_classes.Extraction).all()

        assert len(all_results) == 26

        state_entry = ds.session.query(ds.db_classes.State).first()

        extractions_for_state = (
            ds.session.query(ds.db_classes.Extraction)
            .filter(ds.db_classes.Extraction.entry_id == state_entry.state_id)
            .all()
        )

        assert len(extractions_for_state) == 6

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
                "field": "name",
                "importer": "GPX Format Importer",
                "interpreted_value": "NELSON",
                "text": "NELSON",
                "text_location": "450-456",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "timestamp",
                "importer": "GPX Format Importer",
                "interpreted_value": "2012-04-27 15:29:38",
                "text": "2012-04-27T16:29:38+01:00",
                "text_location": "564-589",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "location",
                "importer": "GPX Format Importer",
                "interpreted_value": "-21.698, 22.186",
                "text": '<p:trkpt lat="22.1862861" lon="-21.6978806">\n' "\t\t\t\t",
                "text_location": "482-531",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "course",
                "importer": "GPX Format Importer",
                "interpreted_value": "268.7 degree",
                "text": "268.7",
                "text_location": "613-618",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "speed",
                "importer": "GPX Format Importer",
                "interpreted_value": "4.5 meter / second",
                "text": "4.5",
                "text_location": "643-646",
            },
            {
                "datafile_id": datafile_id,
                "destination_table": "States",
                "entry_id": entry_id,
                "field": "elevation",
                "importer": "GPX Format Importer",
                "interpreted_value": "0.0 meter",
                "text": "0.000",
                "text_location": "538-543",
            },
        ]
