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
        return "S4_TRACK" in filename.upper()

    def can_load_this_header(self, header):
        return header.startswith("RECORD#,REC_DATE,REC_TIME")

    def can_load_this_file(self, file_contents):
        return True

    # TODO:
    # - Date time handling
    # - Platform / sensor (will need to ask for platform)
    # - Determine which of the file formats we've actually got
    # Will need to check the data to see if there is a difference in length
    # Otherwise, will need to get column names
    # - Read in ownship positions
    # - Read in tracks/contacts

    # Some complexities:
    # - We have two different formatted files (Sept 20 / Jan 21 formatted one way, Mar 21 formatted differently)
    # - Full Shore format has a range of different sources of data, with any
    # being present on a row (but only one present per row) so ownship tracks
    # are mixed up with contacts
    #    - To minimise possible issues with classification of importer,
    #    check if ownship and then parse everything else as contacts
    # - There are a lot of columns in these data files, with lots of the important
    # ones being towards the end of the table. This may cause issues with the
    # hightlighting.
