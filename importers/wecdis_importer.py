from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class WecdisImporter(Importer):
    def __init__(self):
        super().__init__(
            name="WECDIS File Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="WECDIS Importer",
            datafile_type="WECDIS",
        )

        self.platform_name = None

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
            # Always skip the $POSL tag [0]
            msg_type = tokens[1].text
            print(msg_type)

    def handle_vnm(self, vnm_tokens):
        """Extracts the important information from a VNM line
        :param vnm_tokens: A tokenised VNM line
        :ptype vnm_tokens: Line (list of tokens)"""
        if len(vnm_tokens) < 3:
            self.errors.append(
                {
                    self.error_type: f"VNM line does not contain enough parts. No platform name in {vnm_tokens}"
                }
            )
            return  # Not necessarily an error, but can't do anything with it now
        if vnm_tokens[1].text != "VNM":
            # Programming error, shouldn't be hit but if it does we're passing the wrong line
            raise TypeError(f"Expected a VNM line, given {vnm_tokens[1].text}")
        self.platform_name, _, _ = vnm_tokens[2].text.partition(
            "*"
        )  # Ignore the *XX part if present
