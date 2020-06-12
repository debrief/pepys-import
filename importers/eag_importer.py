import os
from datetime import datetime

from tqdm import tqdm

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed


class EAGImporter(Importer):
    def __init__(self):
        super().__init__(
            name="EAG Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="EAG Importer",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".EAG.TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_object, datafile, change_id):
        filename, ext = os.path.splitext(os.path.basename(path))

        try:
            date_of_recording_str, callsign = filename.split("_")
        except ValueError:
            self.errors.append(
                {self.error_type: f"Error in filename - cannot extract date and callsign"}
            )
            return

        # Get date of last Sunday
        try:
            last_sun_date = self.get_last_sunday(date_of_recording_str)
        except Exception:
            self.errors.append({self.error_type: f"Error in filename - cannot parse date"})
            return

        for line_number, line in enumerate(tqdm(file_object.lines()), 1):
            tokens = line.tokens(line.WHITESPACE_DELIM)

            if len(tokens) != 11:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {line_number}. Incorrect number of tokens: {line}"
                    }
                )
                continue

            # separate token strings
            time_since_sun_ms_token = tokens[0]
            ecef_x_token = tokens[4]
            ecef_y_token = tokens[5]
            ecef_z_token = tokens[6]
            heading_token = tokens[9]

            try:
                time_since_sun_ms = float(time_since_sun_ms_token.text())
            except ValueError:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {line_number}. Cannot parse time since Sunday to float: {line}"
                    }
                )
                continue

            timestamp = self.calculate_timestamp(time_since_sun_ms, last_sun_date)
            time_since_sun_ms_token.record(self.name, "timestamp", timestamp)

            # and finally store it
            platform = data_store.get_platform(platform_name=callsign, change_id=change_id,)

            # TODO: Do we have a fixed sensor type for these files?
            sensor_type = data_store.add_to_sensor_types("GPS", change_id=change_id).name
            # TODO: Or a fixed sensor name?
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name="E-Trac",
                sensor_type=sensor_type,
                privacy="Public",
                change_id=change_id,
            )
            state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

            location, success = self.convert_ecef_to_location(
                ecef_x_token, ecef_y_token, ecef_z_token
            )

            if success:
                state.location = location
                combine_tokens(ecef_x_token, ecef_y_token, ecef_z_token).record(
                    self.name, "location", state.location, "ECEF X, Y and Z"
                )

            elevation_valid, elevation = convert_distance(
                altitude_token.text, unit_registry.metre, line_number, self.errors, self.error_type
            )
            if elevation_valid:
                state.elevation = elevation
                altitude_token.record(self.name, "altitude", state.elevation)

            heading_valid, heading = convert_absolute_angle(
                heading_token.text, line_number, self.errors, self.error_type
            )
            if heading_valid:
                state.heading = heading
                heading_token.record(self.name, "heading", heading)

            speed_valid, speed = convert_speed(
                speed_token.text, unit_registry.knots, line_number, self.errors, self.error_type,
            )
            if speed_valid:
                state.speed = speed
                speed_token.record(self.name, "speed", speed)

    def get_last_sunday(self, date_of_recording_str):
        format_str = "%Y%m%d"
        date_of_recording = datetime.datetime.strptime(date_of_recording_str, format_str)

        sun_offset = (date_of_recording.weekday() - 6) % 7

        last_sun = date_of_recording - datetime.timedelta(days=sun_offset)

        return last_sun

    def calculate_timestamp(self, time_since_sun_ms, last_sun_date):
        timestamp = last_sun_date + datetime.timedelta(milliseconds=time_since_sun_ms)

    def convert_ecef_to_location(self, ecef_x_token, ecef_y_token):

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_success = location.set_latitude_decimal_degrees(lat_degrees_token.text)
        lon_success = location.set_longitude_decimal_degrees(long_degrees_token.text)
