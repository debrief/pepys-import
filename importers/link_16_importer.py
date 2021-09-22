from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer

class Link16Importer(Importer):
    def __init__(self):
        super().__init__(
            name="Link-16 Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Link-16 Importer",
            default_privacy="Private",
            datafile_type="Link-16"
        )

        ''' 
        Link-16 has (at least?) two versions that MWC would like to import. 
        Looking at MWC parser, we're expecting to extract the following fields (present in both versions):
          - Name {v1: [2], v2: [4]}
          - Symbol?
          - Lat {v1: [8], v2: [13]}
          - Lon {v1: [7], v2: [14]} # Yes, they did swap Lat/lon between versions...
          - Course {v1: [11], v2: [16]} - deg
          - Speed {v1: [12], v2: [17]} - ft
          - Depth (Altitude) {v1: [10], v2: [15]} - ft

          We also have a date/time - which is offset from a user input start date/time. 
          This date time is in position [1] in both versions of the file
        '''