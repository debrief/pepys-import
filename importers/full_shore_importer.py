import math
from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.level import HighlightLevel
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

DELETE = "eUM_DELETE"
OWNSHIP = "OWN_SHIP"
LATITUDE = "Latitude"
LONGITUDE = "Longitude"
DEPTH = "Depth"
SPEED = "Speed"
COURSE = "Course"
NAME_P1 = "Name_P1"
NAME_P2 = "Name_P2"


class FullShoreImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Full Shore Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Full Shore Importer",
            datafile_type="Full Shore",
            default_privacy="Private",
        )
        self.platform = None
        self.set_highlighting_level(HighlightLevel.NONE)

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("RECORD#,REC_DATE,REC_TIME")

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line_number == 1:
            # Skip the header & make sure we reset platform between files (may not be the same)
            self.platform = None
            return

        tokens = line.tokens(line.CSV_TOKENISER, ",")

        # Check length first because we're reliant on positions in the line
        if len(tokens) != 1933 and len(tokens) != 1986:
            # Invalid line length (based on the files we've got so far...)
            self.errors.append(
                {
                    self.error_type: f"Error on line {line_number}. Unable to read Full Shore with {len(tokens)} tokens"
                }
            )
            return

        # Date time parsing common to both file formats
        date_token = tokens[1]
        time_token = tokens[2]
        timestamp = self.parse_timestamp(tokens[1].text, tokens[2].text)
        combine_tokens(date_token, time_token).record(self.name, "timestamp", timestamp)

        operation_token = tokens[4]
        if operation_token.text == DELETE:
            return  # We're ignoring deletions

        # id_token = tokens[9] - TODO - work out whether this is a unique track num
        source_token = tokens[10]

        if source_token.text == OWNSHIP:
            # Ask for the platform & hold onto it
            self.platform = self.get_cached_platform(
                data_store, platform_name=OWNSHIP, change_id=change_id
            )

        sensor_type = data_store.add_to_sensor_types(source_token.text, change_id).name
        privacy = get_lowest_privacy(data_store)
        # The data we've got indicates that Ownship is always first, so this should be ok
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=source_token.text,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )

        # The positions of many tokens vary between two formats
        selected_tokens = {}
        if len(tokens) == 1986:
            # If we've got original geo data use that, otherwise use Point TMS
            selected_tokens[LATITUDE] = tokens[1225] if tokens[1231].text else tokens[1272]
            selected_tokens[LONGITUDE] = tokens[1226] if tokens[1232].text else tokens[1273]
            selected_tokens[DEPTH] = tokens[1233] if tokens[1233].text else tokens[1274]
            selected_tokens[COURSE] = tokens[1231] if tokens[1237].text else tokens[1266]
            selected_tokens[SPEED] = tokens[1232] if tokens[1238].text else tokens[1267]
            if tokens[1474].text:
                selected_tokens[NAME_P1] = tokens[1474]
                selected_tokens[NAME_P2] = tokens[1464]
            else:
                selected_tokens[NAME_P1] = tokens[1483]
                selected_tokens[NAME_P2] = tokens[10]
        elif len(tokens) == 1933:
            selected_tokens[LATITUDE] = tokens[1184] if tokens[1184].text else tokens[1231]
            selected_tokens[LONGITUDE] = tokens[1185] if tokens[1185].text else tokens[1232]
            selected_tokens[DEPTH] = tokens[1186] if tokens[1186].text else tokens[1233]
            selected_tokens[COURSE] = tokens[1190] if tokens[1190].text else tokens[1225]
            selected_tokens[SPEED] = tokens[1191] if tokens[1191].text else tokens[1226]
            if tokens[1433].text:
                selected_tokens[NAME_P1] = tokens[1433]
                selected_tokens[NAME_P2] = tokens[10]
            else:
                selected_tokens[NAME_P1] = tokens[1442]
                selected_tokens[NAME_P2] = tokens[10]

        if source_token.text == OWNSHIP:
            self.parse_ownship_state(
                data_store, datafile, line_number, sensor, timestamp, selected_tokens
            )
        else:
            self.parse_contact(
                data_store, datafile, line_number, sensor, timestamp, selected_tokens
            )

        datafile.flush_extracted_tokens()

    def parse_ownship_state(self, data_store, datafile, line_number, sensor, timestamp, tokens):
        """Parse a full shore recorded ownship state
        :param data_store: The data store that this is importing into
        :param datafile: The datafile being imported
        :param line_number: The number of the line currently being imported
        :param sensor: The sensor associated with this state update
        :param timestamp: The timestamp of this state change
        :param tokens: The tokens that we are using to generate this state
        :ptype tokens: A dictionary of name/token pairs e.g. "lat": latitude_token
        """
        lat_token = tokens[LATITUDE]
        lon_token = tokens[LONGITUDE]
        height_token = tokens[DEPTH]
        speed_token = tokens[SPEED]
        course_token = tokens[COURSE]
        state = datafile.create_state(data_store, self.platform, sensor, timestamp, self.short_name)

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_degs = math.degrees(float(lat_token.text))
        lon_degs = math.degrees(float(lon_token.text))
        lat_success = location.set_latitude_decimal_degrees(lat_degs)
        lon_success = location.set_longitude_decimal_degrees(lon_degs)
        if lat_success and lon_success:
            state.location = location
            combine_tokens(lat_token, lon_token).record(
                self.name, "location", state.location, "decimal radians"
            )
        if height_token.text:
            elevation_valid, elevation = convert_distance(
                height_token.text, unit_registry.meter, line_number, self.errors, self.error_type
            )
            if elevation_valid:
                state.elevation = elevation
                height_token.record(self.name, "altitude", state.elevation)
        if course_token.text:
            # TODO - check format of this angle (might be rads)
            heading_degs = math.degrees(float(course_token.text))
            heading_valid, heading = convert_absolute_angle(
                heading_degs, line_number, self.errors, self.error_type
            )
            if heading_valid:
                state.heading = heading
                course_token.record(self.name, "heading", heading)
        if speed_token.text:
            speed_valid, speed = convert_speed(
                speed_token.text, unit_registry.knot, line_number, self.errors, self.error_type
            )
            if speed_valid:
                state.speed = speed
                speed_token.record(self.name, "speed", speed)

    def parse_contact(self, data_store, datafile, line_number, sensor, timestamp, tokens):
        """Parse a full shore recorded contact
        :param data_store: The data store that this is importing into
        :param datafile: The datafile being imported
        :param line_number: The number of the line currently being imported
        :param sensor: The sensor that detected this contact
        :param timestamp: The timestamp of this contact detection
        :param tokens: The tokens that we are using to generate this contact
        :ptype tokens: A dictionary of name/token pairs e.g. "lat": latitude_token
        """
        lat_token = tokens[LATITUDE]
        lon_token = tokens[LONGITUDE]
        height_token = tokens[DEPTH]
        speed_token = tokens[SPEED]
        course_token = tokens[COURSE]
        name_p1_token = tokens[NAME_P1]
        name_p2_token = tokens[NAME_P2]
        contact = datafile.create_contact(
            data_store, self.platform, sensor, timestamp, self.short_name
        )

        contact.track_number = name_p1_token.text + "_" + name_p2_token.text
        combine_tokens(name_p1_token, name_p2_token).record(
            self.name, "track name", contact.track_number
        )

        # We may not have a latitude/longitude
        if lat_token.text and lon_token.text:
            location = Location(errors=self.errors, error_type=self.error_type)
            lat_degs = math.degrees(float(lat_token.text))
            lon_degs = math.degrees(float(lon_token.text))
            lat_success = location.set_latitude_decimal_degrees(lat_degs)
            lon_success = location.set_longitude_decimal_degrees(lon_degs)
            if lat_success and lon_success:
                contact.location = location
                combine_tokens(lat_token, lon_token).record(
                    self.name, "location", contact.location, "decimal radians"
                )
        if height_token.text:
            elevation_valid, elevation = convert_distance(
                height_token.text, unit_registry.meter, line_number, self.errors, self.error_type
            )
            if elevation_valid:
                contact.elevation = elevation
                height_token.record(self.name, "altitude", contact.elevation)
        if course_token.text:

            # TODO - check format of this angle (might be rads)
            bearing_degs = math.degrees(float(course_token.text))
            bearing_valid, bearing = convert_absolute_angle(
                bearing_degs, line_number, self.errors, self.error_type
            )
            if bearing_valid:
                contact.bearing = bearing
                course_token.record(self.name, "bearing", bearing)
        if speed_token.text:
            speed_valid, speed = convert_speed(
                speed_token.text, unit_registry.knot, line_number, self.errors, self.error_type
            )
            if speed_valid:
                contact.speed = speed
                speed_token.record(self.name, "speed", speed)

    @staticmethod
    def parse_timestamp(date, time):
        """Parses the fullshore timestamp from a date & time string
        :param date: The date part of the timestamp
        :type date: String
        :param time: The time part of the timestamp
        :type time: String
        :return a datetime (GMT/UTC/Zulu) if conversion successful
            or None if unsuccessful
        :rtype: datetime | None
        """
        timestamp_format = "%d/%m/%Y %H:%M:%S"
        timestamp_string = f"{date} {time}"
        try:
            res = datetime.strptime(timestamp_string, timestamp_format)
        except ValueError:
            return None
        return res
