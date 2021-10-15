from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class OrcaImporter(Importer):
    """Importer for data exported from the Oceanographic Reconnaissance and Combat
    Architecture (ORCA) system.
    """

    def __init__(self):
        super().__init__(
            name="ORCA Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="ORCA Importer",
            default_privacy="Private",
            datafile_type="ORCA",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".XML"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        # TODO - confirm this is actually the header
        return header.startswith('<ns2:datafile xmlns:ns2="mw">')

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # TODO:
        # - Read in the file
        # - Parse the platform
        # - Parse the tracks
        pass
