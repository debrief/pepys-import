from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class WECDISImporter(Importer):
    def __init__(self):
        super().__init__(
            name="WECDIS File Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="WECDIS Importer",
            datafile_type="WECDIS",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header) -> bool:
        return super().can_load_this_header(header)

    def can_load_this_file(self, file_contents) -> bool:
        return super().can_load_this_file(file_contents)

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):

        tokens = line.tokens(line.CSV_TOKENISER, ",")

        if len(tokens) > 1:
            msg_type = tokens[1].text
            print(msg_type)
