from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed


class ETracImporter(Importer):
    def __init__(
        self,
        name="E-Trac Format Importer",
        validation_level=constants.BASIC_LEVEL,
        short_name="E-Trac Importer",
        separator=" ",
    ):
        super().__init__(name, validation_level, short_name)
        self.separator = separator

        self.text_label = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("!Target,MMSI")

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        # Skip the header
        if line_number == 1:
            return

        tokens = line.tokens(line.CSV_DELIM, ",")
        if len(tokens) <= 1:
            # the last line may be empty, don't worry
            return
        if len(tokens) < 17:
            self.errors.append(
                {self.error_type: f"Error on line {line_number}. Not enough tokens: {line}"}
            )
            return

        # separate token strings
        date_token = tokens[2]
        time_token = tokens[3]
        lat_degrees_token = tokens[4]
        long_degrees_token = tokens[5]
        heading_token = tokens[8]
        altitude_token = tokens[10]
        speed_token = tokens[6]
        comp_name_token = tokens[18]

        vessel_name = self.name_for(comp_name_token.text)
        comp_name_token.record(self.name, "vessel name", vessel_name)

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
                    self.error_type: f"Line {line_number}. Error in Date format '{time_token.text}'."
                    "Should be HH:mm:ss"
                }
            )
            return

        timestamp = self.parse_timestamp(date_token.text, time_token.text)
        combine_tokens(date_token, time_token).record(self.name, "timestamp", timestamp)

        # and finally store it
        platform = data_store.get_platform(
            platform_name=vessel_name,
            nationality="UK",
            platform_type="Fisher",
            privacy="Public",
            change_id=change_id,
        )
        sensor_type = data_store.add_to_sensor_types("GPS", change_id=change_id)
        privacy = data_store.missing_data_resolver.resolve_privacy(data_store, change_id)
        sensor = platform.get_sensor(
            data_store=data_store,
            sensor_name="E-Trac",
            sensor_type=sensor_type,
            privacy=privacy.name,
            change_id=change_id,
        )
        state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)
        state.privacy = privacy.privacy_id

        location = Location(errors=self.errors, error_type=self.error_type)
        location.set_latitude_decimal_degrees(lat_degrees_token.text)
        location.set_longitude_decimal_degrees(long_degrees_token.text)
        state.location = location

        combine_tokens(long_degrees_token, lat_degrees_token).record(
            self.name, "location", state.location, "decimal degrees"
        )

        state.elevation = altitude_token.text * unit_registry.metre
        altitude_token.record(self.name, "altitude", state.elevation)

        heading = convert_absolute_angle(
            heading_token.text, line_number, self.errors, self.error_type
        )
        state.heading = heading
        heading_token.record(self.name, "heading", heading)

        speed = convert_speed(
            speed_token.text, unit_registry.knots, line_number, self.errors, self.error_type,
        )
        if speed:
            state.speed = speed
        speed_token.record(self.name, "speed", speed)

    @staticmethod
    def name_for(token):
        # split into two
        tokens = token.split()
        return tokens[1]

    @staticmethod
    def parse_timestamp(date, time):
        format_str = "%Y/%m/%d "
        format_str += "%H:%M:%S"

        res = datetime.strptime(date.strip() + " " + time.strip(), format_str)

        return res
