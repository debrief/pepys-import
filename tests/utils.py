import os

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from pepys_import.utils.text_formatting_utils import formatted_text_to_str


def check_errors_for_file_contents(file_contents, expected_errors, importer, filename=None):
    data_store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    data_store.initialise()

    processor = FileProcessor(archive=False)
    processor.register_importer(importer)

    # check states empty
    with data_store.session_scope():
        # there must be no states at the beginning
        states = data_store.session.query(data_store.db_classes.State).all()
        assert len(states) == 0

        # there must be no platforms at the beginning
        platforms = data_store.session.query(data_store.db_classes.Platform).all()
        assert len(platforms) == 0

        # there must be no datafiles at the beginning
        datafiles = data_store.session.query(data_store.db_classes.Datafile).all()
        assert len(datafiles) == 0

    if filename is None:
        filename = "test_input.txt"

    with open(filename, "w") as f:
        f.write(file_contents)

    # parse the file
    processor.process(filename, data_store, False)

    # Delete the temporary file
    os.remove(filename)

    # check data got created
    with data_store.session_scope():
        # there must be no states
        states = data_store.session.query(data_store.db_classes.State).all()
        assert len(states) == 0

    errors = processor.importers[0].errors

    if expected_errors is None:
        assert len(errors) == 0
        return

    if len(errors) == 0:
        assert False, "No errors reported"
    errors = errors[0]

    joined_errors = "\n".join(errors.values())

    if isinstance(expected_errors, str):
        assert expected_errors in joined_errors
    else:
        for expected_error in expected_errors:
            assert expected_error in joined_errors


def move_and_overwrite(from_path, to_path):
    """
    Moves a file from from_path to to_path, overwriting the destination file if it already exists.

    Does this by deleting the to_path if it already exists, then doing the move
    """
    if os.path.exists(to_path):
        os.remove(to_path)

    os.rename(from_path, to_path)


# Use normal print() to capture table reports
def side_effect(text):
    print(formatted_text_to_str(text))
