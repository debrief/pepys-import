# from pepys_import.core.formats import unit_registry
# from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer

# from pepys_import.file.highlighter.support.combine import combine_tokens
# from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

V1_HEADER = "PPLI"
V2_HEADER = "Xmt/Rcv"


class Link16Importer(Importer):
    """Importer to handle two different formats of track information that are
    transmitted using Link-16 encoding
    """

    def __init__(self):
        super().__init__(
            name="Link-16 Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Link-16 Importer",
            default_privacy="Private",
            datafile_type="Link-16",
        )
        self.version = 1

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        # V1 starts w/ PPLI
        # V2 starts w/ Xmt/Rcv
        return header.startswith(V1_HEADER) or header.startswith(V2_HEADER)

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line_number == 1:
            # Will only parse if one of these headers found
            self.version = 1 if line.startswith(V1_HEADER) else 2
            return
        tokens = line.tokens(line.CSV_TOKENISER, ",")
        if len(tokens) <= 1:
            # To skip over any blank lines
            return

        if self.version == 1:
            if len(tokens) < 15:
                self.errors.append(
                    {self.error_type: f"Error on line {line_number}. Not enough tokens: {line}"}
                )
                return

            # lat_degrees_token = tokens[8]
            # lon_degrees_token = tokens[7]
            # heading_token = tokens[11]
            # speed_token = tokens[12]
            # altitude_token = tokens[10]

        elif self.version == 2:
            raise NotImplementedError()

        # state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

        # location = Location(errors=self.errors, error_type=self.error_type)
        # lat_success = location.set_latitude_decimal_degrees(lat_degrees_token.text)
        # lon_success = location.set_longitude_decimal_degrees(lon_degrees_token.text)
        # if lat_success and lon_success:
        # state.location = location
        # combine_tokens(lon_degrees_token, lat_degrees_token).record(
        #     self.name, "location", state.location, "decimal degrees"
        # )

        # elevation_valid, elevation = convert_distance(
        #     altitude_token.text, unit_registry.foot, line_number, self.errors, self.error_type
        # )

        # if elevation_valid:
        #     state.elevation = elevation
        #     altitude_token.record(self.name, "altitude", state.elevation)

        # heading_valid, heading = convert_absolute_angle(
        #     heading_token.text, line_number, self.errors, self.error_type
        # )
        # if heading_valid:
        #     state.heading = heading
        #     heading_token.record(self.name, "heading", heading)

        # speed_valid, speed = convert_speed(
        #     speed_token.text,
        #     unit_registry.feet_per_second,
        #     line_number,
        #     self.errors,
        #     self.error_type,
        # )
        # if speed_valid:
        #     state.speed = speed
        #     speed_token.record(self.name, "speed", speed)

    """
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
    """
