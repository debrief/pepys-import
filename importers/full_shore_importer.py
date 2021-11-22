from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class FullShoreImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Full Shore Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Full Shore Importer",
            datafile_type="Full Shore",
            default_privacy="Private",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        pass
        # TBC - return

    def can_load_this_file(self, file_contents):
        return True
