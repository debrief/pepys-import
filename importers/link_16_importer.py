import os
from datetime import datetime, timedelta

from tqdm import tqdm

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import CANCEL_IMPORT, Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
)
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

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

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # Read the base timestamp from the filename
        filename, ext = os.path.splitext(os.path.basename(path))
        datetime_string = self.extract_timestamp(filename)
        self.base_timestamp = self.timestamp_to_datetime(datetime_string)
        self.current_hour = 0
        self.previous_time = timedelta(hours=0, minutes=0, seconds=0)

        # Now do what we'd normally do on load
        for line_number, line in enumerate(tqdm(file_object.lines()), 1):
            result = self._load_this_line(data_store, line_number, line, datafile, change_id)
            if result == CANCEL_IMPORT:
                custom_print_formatted_text(
                    format_error_message(f"Error in file caused cancellation of import of {path}")
                )
                break

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line_number == 1:
            # Will only parse if one of these headers found
            self.version = 1 if line.text.startswith(V1_HEADER) else 2
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
            name_token = tokens[2]
            lat_degrees_token = tokens[8]
            lon_degrees_token = tokens[7]
            heading_token = tokens[11]
            speed_token = tokens[12]
            altitude_token = tokens[10]

        elif self.version == 2:
            if len(tokens) < 28:
                self.errors.append(
                    {self.error_type: f"Error on line {line_number}. Not enough tokens: {line}"}
                )
                return
            name_token = tokens[4]
            lat_degrees_token = tokens[13]
            lon_degrees_token = tokens[14]
            heading_token = tokens[16]
            speed_token = tokens[17]
            altitude_token = tokens[15]

        # Time wrangling - TODO - consider extracting into a method
        time_token = tokens[1]
        # The time as MM:SS.MS as read in from the file
        line_time = timedelta(
            hours=0,
            minutes=int(time_token.text[:2]),
            seconds=float(time_token.text[3:]),
        )
        # Has time gone down from the last? If so, we've shifted an hour forwards
        if line_time < self.previous_time:
            self.current_hour += 1

        self.previous_time = line_time
        # Turn the time from MM:SS.MS to HH:MM:SS.MS
        line_time += timedelta(hours=self.current_hour)
        # Offset the parsed time relative to the file's timestamp
        line_time += self.base_timestamp

        # -- TODO - Confirm that this is correct for this data
        platform = self.get_cached_platform(
            data_store, platform_name=name_token.text, change_id=change_id
        )
        # TODO - confirm the actual sensor type
        sensor_type = data_store.add_to_sensor_types("Location-Link16", change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = platform.get_sensor(
            data_store=data_store,
            sensor_name="Link-16",
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        # -- END TODO
        state = datafile.create_state(data_store, platform, sensor, line_time, self.short_name)

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_success = location.set_latitude_decimal_degrees(lat_degrees_token.text)
        lon_success = location.set_longitude_decimal_degrees(lon_degrees_token.text)
        if lat_success and lon_success:
            state.location = location
            combine_tokens(lon_degrees_token, lat_degrees_token).record(
                self.name, "location", state.location, "decimal degrees"
            )

        elevation_valid, elevation = convert_distance(
            altitude_token.text, unit_registry.foot, line_number, self.errors, self.error_type
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
            speed_token.text,
            unit_registry.foot_per_second,
            line_number,
            self.errors,
            self.error_type,
        )
        if speed_valid:
            state.speed = speed
            speed_token.record(self.name, "speed", speed)

    @staticmethod
    def extract_timestamp(filename):
        """Extracts a Link-16 timestamp from an unmodified filename
        :param filename: The Link-16 filename that contains a timestamp
        :type filename: String
        :return: The timestamp extracted from the filename
        :rtype: String
        """
        # TODO - confirm that there is always a double extension
        base_filename, ext = os.path.splitext(os.path.basename(filename))
        base_filename, ext = os.path.splitext(base_filename)
        # TODO - confirm the timestamp always just before the file extension
        extracted_datetime = base_filename[-19:]
        return extracted_datetime

    @staticmethod
    def timestamp_to_datetime(timestamp_string):
        """Converts a Link-16 formatted timestamp into a Python datetime
        :param timestamp_string: The Link16 file timestamp
        :type timestamp_string: String
        :return: a datetime if conversion successful or False if unsuccessful
        :rtype: datetime | bool
        """
        timestamp_format = "%d-%m-%YT%H-%M-%S"
        try:
            res = datetime.strptime(timestamp_string, timestamp_format)
        except ValueError:
            return False
        return res
