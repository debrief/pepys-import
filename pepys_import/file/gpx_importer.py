from .importer import Importer
from datetime import datetime
from pepys_import.core.formats import unit_registry
from pepys_import.utils.unit_utils import convert_heading, convert_speed


class GPXImporter(Importer):
    name = "GPX Format Importer"

    def __init__(self, separator=" "):
        super().__init__()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".GPX"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        # Can't tell from first line only whether file is a valid GPX file
        return True

    def can_load_this_file(self, file_contents):
        # TODO: Check here to see if we can parse file with XML parser
        return True

    def load_this_file(self, data_store, path, file_contents, data_file_id):
        print("GPX parser working on ", path)
