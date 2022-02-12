from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.level import HighlightLevel
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed


class AIS_MarineCadastre_Importer(Importer):
    """Imports AIS data from https://marinecadastre.gov/ais/"""

    def __init__(self):
        super().__init__(
            name="AIS Marine Cadastre Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="AIS Marine Cadastre Importer",
            default_privacy="Public",
            datafile_type="AIS",
        )
        self.text_label = None

        self.set_highlighting_level(HighlightLevel.NONE)

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return "MMSI,BaseDateTime" in header

    def can_load_this_file(self, file_contents):
        return True

    # @profile
    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        # Skip the header
        if line_number == 1:
            return

        tokens = line.tokens(line.CSV_TOKENISER, ",")
        if len(tokens) <= 1:
            # the last line may be empty, don't worry
            return
        if len(tokens) < 17:
            self.errors.append(
                {self.error_type: f"Error on line {line_number}. Not enough tokens: {line}"}
            )
            return

        # separate token strings
        datetime_token = tokens[1]
        lat_degrees_token = tokens[2]
        long_degrees_token = tokens[3]
        speed_token = tokens[4]
        course_token = tokens[5]
        heading_token = tokens[6]
        name_token = tokens[7]
        imo_id_token = tokens[8]

        imo_id = imo_id_token.text
        imo_id_token.record(self.name, "imo_id", imo_id)

        vessel_name = name_token.text
        name_token.record(self.name, "vessel name", vessel_name)

        if len(datetime_token.text) != 19:
            self.errors.append(
                {
                    self.error_type: f"Error on line {line_number}. Datetime format '{datetime_token.text}' "
                    f"should be 19 characters long"
                }
            )
            return

        timestamp = self.parse_timestamp(datetime_token.text)
        if timestamp:
            datetime_token.record(self.name, "timestamp", timestamp)
        else:
            # Skip line if invalid timestamp
            self.errors.append(
                {self.error_type: f"Line {line_number}. Error in timestamp parsing."}
            )
            return

        if imo_id.strip() != "" and imo_id.strip() != "IMO0000000":
            plat_name = imo_id
        else:
            if vessel_name.strip() != "":
                plat_name = vessel_name
            else:
                plat_name = None

        # and finally store it
        platform = self.get_cached_platform(
            data_store, platform_name=plat_name, change_id=change_id, unknown=True
        )
        sensor_type = data_store.add_to_sensor_types("Broadcast", change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = platform.get_sensor(
            data_store=data_store,
            sensor_name="AIS",
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_success = location.set_latitude_decimal_degrees(lat_degrees_token.text)
        lon_success = location.set_longitude_decimal_degrees(long_degrees_token.text)
        if lat_success and lon_success:
            state.location = location
            combine_tokens(long_degrees_token, lat_degrees_token).record(
                self.name, "location", state.location, "decimal degrees"
            )

        heading_valid, heading = convert_absolute_angle(
            heading_token.text, line_number, self.errors, self.error_type
        )
        if heading_valid:
            state.heading = heading
            heading_token.record(self.name, "heading", heading)

        course_valid, course = convert_absolute_angle(
            course_token.text, line_number, self.errors, self.error_type
        )
        if course_valid:
            state.course = course
            course_token.record(self.name, "course", course)

        speed_valid, speed = convert_speed(
            speed_token.text,
            unit_registry.knots,
            line_number,
            self.errors,
            self.error_type,
        )
        if speed_valid:
            state.speed = speed
            speed_token.record(self.name, "speed", speed)

        datafile.flush_extracted_tokens()

    @staticmethod
    def parse_timestamp(datetime_str):
        # Parses the following format
        # 2020-01-01T00:00:00
        try:
            res = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return False

        return res
