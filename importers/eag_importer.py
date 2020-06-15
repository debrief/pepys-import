import datetime
import math
import os

from tqdm import tqdm

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle


class EAGImporter(Importer):
    def __init__(self):
        # The TIME_OFFSET is a value in seconds to be added to
        # the timestamp value calculated from the 'milliseconds since Sunday'
        # column (Column A). This defaults to zero, but can be altered
        # to adjust the time value so it matches Column K
        # For example, TIME_OFFSET of -16, will subtract 16 seconds from
        # the calculated time, which would mean it would match the
        # GPS time in Column K
        self.TIME_OFFSET = 0
        super().__init__(
            name="EAG Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="EAG Importer",
        )

    # EAG files end with .eag.txt
    # BUT, can_load_this_type only provides the file extension
    # which the Python splitext function thinks is .TXT - as it just
    # looks for the last dot.
    # Therefore, we check for a file extension of .TXT AND
    # a filename ending with .EAG (in the next function)
    def can_load_this_type(self, suffix):
        return suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return filename.upper().endswith(".EAG")

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        filename, ext = os.path.splitext(os.path.basename(path))

        # Extract date of recording and callsign from filename
        try:
            date_of_recording_str, callsign = filename.split("_")
        except ValueError:
            self.errors.append(
                {self.error_type: f"Error in filename - cannot extract date and callsign"}
            )
            return

        # Get date of last Sunday, ready for timestamp calculation later
        try:
            last_sun_date = self.get_previous_sunday(date_of_recording_str)
        except Exception:
            self.errors.append(
                {self.error_type: f"Error in filename - cannot parse date {date_of_recording_str}"}
            )
            return

        for line_number, line in enumerate(tqdm(file_object.lines()), 1):
            if line.text.strip().startswith("#VALUE"):
                # Skip line
                continue
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
                time_since_sun_ms = float(time_since_sun_ms_token.text)
            except ValueError:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {line_number}. Cannot parse time since Sunday to float: {line}"
                    }
                )
                continue

            # Calculate the timestamp, using the time since last Sunday and the calculated last Sunday date
            timestamp = self.calculate_timestamp(time_since_sun_ms, last_sun_date)
            time_since_sun_ms_token.record(self.name, "timestamp", timestamp)

            # Platform is based on the callsign - the user will link this as a synonym to a defined Platform
            platform = data_store.get_platform(platform_name=callsign, change_id=change_id,)

            # Sensor Type is always fixed to GPS
            sensor_type = data_store.add_to_sensor_types("GPS", change_id=change_id).name
            sensor = platform.get_sensor(
                data_store=data_store, sensor_type=sensor_type, change_id=change_id,
            )
            state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

            # Location and height info are provided as Earth-Centred, Earth-Fixed co-ordinates
            # We convert them to lat/lon and height
            location, height, success = self.convert_ecef_to_location_and_height(
                ecef_x_token, ecef_y_token, ecef_z_token
            )

            if success:
                state.location = location
                combine_tokens(ecef_x_token, ecef_y_token, ecef_z_token).record(
                    self.name, "location", state.location, "ECEF X, Y and Z"
                )

                state.elevation = height * unit_registry.metre
                combine_tokens(ecef_x_token, ecef_y_token, ecef_z_token).record(
                    self.name, "altitude", state.elevation, "ECEF X, Y and Z"
                )
            else:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {line_number}. Cannot parse ECEF X, Y and Z to latitude, longitude and height: {line}"
                    }
                )
                continue

            heading_valid, heading = convert_absolute_angle(
                heading_token.text, line_number, self.errors, self.error_type
            )
            if heading_valid:
                state.heading = heading
                heading_token.record(self.name, "heading", heading)

    def get_previous_sunday(self, date_of_recording_str):
        format_str = "%Y%m%d"
        date_of_recording = datetime.datetime.strptime(date_of_recording_str, format_str)

        sun_offset = (date_of_recording.weekday() - 6) % 7

        last_sun = date_of_recording - datetime.timedelta(days=sun_offset)

        return last_sun

    def calculate_timestamp(self, time_since_sun_ms, last_sun_date):
        timestamp = last_sun_date + datetime.timedelta(milliseconds=time_since_sun_ms)

        timestamp = timestamp + datetime.timedelta(seconds=self.TIME_OFFSET)

        return timestamp

    def convert_ecef_to_location_and_height(self, ecef_x_token, ecef_y_token, ecef_z_token):
        """Converts Earth-Centred, Earth-Fixed X, Y and Z co-ordinates into a Location object containing
        latitude and longitude, plus a height value in metres.

        X, Y and Z should be provided in metres.
        
        All formulae taken from https://microem.ru/files/2012/08/GPS.G1-X-00006.pdf
        """
        ecef_x = float(ecef_x_token.text)
        ecef_y = float(ecef_y_token.text)
        ecef_z = float(ecef_z_token.text)

        # Parameters for WGS-84 ellipsoid
        a = 6378137
        b = 6356752.31424518
        e = math.sqrt((a ** 2 - b ** 2) / (a ** 2))
        e_dash = math.sqrt((a ** 2 - b ** 2) / (b ** 2))

        # Auxilliary values
        p = math.sqrt(ecef_x ** 2 + ecef_y ** 2)
        theta = math.atan((ecef_z * a) / (p * b))

        # Calculate longitude from ECEF X and Y as:
        # longitude = arctan(Y / X)
        longitude = math.degrees(math.atan((ecef_y / ecef_x)))

        top_lat_frac = ecef_z + (e_dash ** 2) * b * (math.sin(theta) ** 3)
        bottom_lat_frac = p - (e ** 2) * a * (math.cos(theta) ** 3)

        latitude = math.degrees(math.atan(top_lat_frac / bottom_lat_frac))

        Ntemp = math.sqrt(1 - (e ** 2) * (math.sin(math.radians(latitude)) ** 2))

        N = a / Ntemp

        height = (p / math.cos(math.radians(latitude))) - N

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_success = location.set_latitude_decimal_degrees(latitude)
        lon_success = location.set_longitude_decimal_degrees(longitude)

        success = lat_success and lon_success
        return location, height, success
