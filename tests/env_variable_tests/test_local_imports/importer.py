from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class TestImporter(Importer):
    def __init__(
        self,
        name="Test Importer",
        validation_level=constants.BASIC_LEVEL,
        short_name="Test",
    ):
        super().__init__(name, validation_level, short_name)
        self.errors = list()

    def can_load_this_header(self, header) -> bool:
        return True

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_type(self, suffix):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_file(self, data_store, path, file_contents, data_file):
        pass
