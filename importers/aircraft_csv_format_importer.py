from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed


class AircraftCsvFormatImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Aircraft CSV Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name=" Aircraft CSV Importer",
            default_privacy="Public",
            datafile_type="CSV",
        )
        self.text_label = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("Date(Uk)")

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        # Skip the header
        if line_number == 1:
            return

        tokens = line.tokens(line.CSV_TOKENISER, ",")
        if len(tokens) <= 1:
            # The last line may be empty, don't worry
            return
        if len(tokens) < 8:
            # CSV example file has 9 columns
            self.errors.append(
                {self.error_type: f"Error on line {line_number}. Not enough tokens: {line}"}
            )
            return

        # Separate token strings
        date_token = tokens[0]
        time_token = tokens[1]
        # lat_token = tokens[2]  # Currently not used
        # long_token = tokens[3]  # Currently not used
        lat_degrees_token = tokens[4]
        long_degrees_token = tokens[5]
        altitude_token = tokens[6]
        speed_token = tokens[7]
        course_token = tokens[8]

        # Check Date is in correct format
        if len(date_token.text) != 10:
            self.errors.append(
                {
                    self.error_type: f"Error on line {line_number}. Date format '{date_token.text}' "
                    f"should be 10 figure data"
                }
            )
            return

        # Times always in Zulu/GMT
        if len(time_token.text) != 8:
            self.errors.append(
                {
                    self.error_type: f"Line {line_number}. Error in Time format '{time_token.text}'."
                    "Should be HH:mm:ss"
                }
            )
            return

        timestamp = self.parse_timestamp(date_token.text, time_token.text)
        if timestamp:
            combine_tokens(date_token, time_token).record(self.name, "timestamp", timestamp)
        else:
            # Skip line if invalid timestamp
            self.errors.append(
                {self.error_type: f"Line {line_number}. Error in timestamp parsing."}
            )
            return

        # And finally store it - Check how to do this as currently don't have a platform name
        platform = self.get_cached_platform(data_store, platform_name=None, change_id=change_id)
        sensor_type = data_store.add_to_sensor_types("Location-Satellite", change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = platform.get_sensor(
            data_store=data_store,
            sensor_name="GPS",
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

        # Set the location conversion
        location = Location(errors=self.errors, error_type=self.error_type)
        print(lat_degrees_token.text)
        print(long_degrees_token.text)
        lat_success = location.set_latitude_decimal_degrees(lat_degrees_token.text)
        lon_success = location.set_longitude_decimal_degrees(long_degrees_token.text)
        if lat_success and lon_success:
            state.location = location
            combine_tokens(long_degrees_token, lat_degrees_token).record(
                self.name, "location", state.location, "decimal degrees"
            )
        else:
            self.errors.append({self.error_type: f"Line {line_number}. Error in Location Parsing."})

        # Convert the altitude and check valid
        elevation_valid, elevation = convert_distance(
            altitude_token.text, unit_registry.metre, line_number, self.errors, self.error_type
        )
        if elevation_valid:
            state.elevation = elevation
            altitude_token.record(self.name, "altitude", state.elevation)

        # Convert the speed and check valid
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

        # Convert the course into Rads and check valid
        course_valid, course = convert_absolute_angle(
            course_token.text, line_number, self.errors, self.error_type
        )
        if course_valid:
            state.course = course
            course_token.record(self.name, "course", course)

    @staticmethod
    def parse_timestamp(date, time):
        format_str = "%d/%m/%Y "
        format_str += "%H:%M:%S"

        try:
            res = datetime.strptime(date.strip() + " " + time.strip(), format_str)
        except ValueError:
            return False

        return res
