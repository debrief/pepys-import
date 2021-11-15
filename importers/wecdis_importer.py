from datetime import datetime
from enum import Enum

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed


class MsgType(str, Enum):
    """The supported WECDIS message types"""

    TIME = "DZA"
    PLATFORM = "VNM"
    CONTACT = "CONTACT"
    POSITION = "CPOS"
    TMA = "TMA"


class WecdisImporter(Importer):
    def __init__(self):
        super().__init__(
            name="WECDIS File Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="WECDIS Importer",
            datafile_type="WECDIS",
        )

        self.platform_name = None
        self.timestamp = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return "$POSL" in header

    def can_load_this_file(self, file_contents):
        # Need to differentiate from general NMEA - so check charts/version available
        contents_string = " ".join(file_contents)
        return "VER" in contents_string and "CHART" in contents_string

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):

        tokens = line.tokens(line.CSV_TOKENISER, ",")
        if len(tokens) > 1:
            # Always skip the $POSL tag [0]
            msg_type = tokens[1].text.upper().strip()
            if msg_type == MsgType.PLATFORM:
                self.handle_vnm(tokens, line_number)
            elif msg_type == MsgType.TIME:
                self.handle_dza(tokens, line_number)
            elif msg_type == MsgType.CONTACT:
                self.handle_contact(data_store, line_number, tokens, datafile, change_id)
            elif msg_type == MsgType.POSITION:
                # Do we have all the information we need?
                if self.platform_name and self.timestamp:
                    self.handle_position(data_store, line_number, tokens, datafile, change_id)
            elif msg_type == MsgType.TMA:
                self.handle_tma(data_store, line_number, tokens, datafile, change_id)
        datafile.flush_extracted_tokens()

    def handle_vnm(self, vnm_tokens, line_number):
        """Extracts the important information from a VNM line
        :param vnm_tokens: A tokenised VNM line
        :ptype vnm_tokens: Line (list of tokens)"""
        if len(vnm_tokens) < 3:
            self.errors.append(
                {self.error_type: f"Not enough parts in line {line_number}. No platform name found"}
            )
            return  # Not necessarily an error, but can't do anything with it now
        if vnm_tokens[1].text != "VNM":
            # Programming error, shouldn't be hit but if it does we're passing the wrong line
            raise TypeError(f"Expected a VNM line, given {vnm_tokens[1].text}")
        # Ignore the *XX part if present
        platform_name_token = vnm_tokens[2]
        self.platform_name, _, _ = platform_name_token.text.partition("*")
        platform_name_token.record(self.name, "platform name", self.platform_name)

    def handle_dza(self, dza_tokens, line_number):
        """Extracts the important information from a DZA (Timestamp) line
        :param dza_tokens: A tokenised DZA line
        :ptype dza_tokens: Line (list of tokens)"""
        if len(dza_tokens) < 4:
            self.errors.append(
                {self.error_type: f"Not enough parts in line {line_number}. No timestamp provided."}
            )
            return
        if dza_tokens[1].text != "DZA":
            raise TypeError(f"Expected a DZA line, given {dza_tokens[1].text}")
        date = dza_tokens[2].text
        time = dza_tokens[3].text
        # TODO - confirm where the timezone is determined (presumably not always GMT)
        self.timestamp = self.parse_timestamp(date, time)
        if not self.timestamp:
            self.errors.append(
                {
                    self.error_type: f"Line {line_number}. Error in timestamp value {date} {time}. "
                    f"Couldn't convert to a datetime"
                }
            )
            return

        timestamp_token = combine_tokens(dza_tokens[2], dza_tokens[3])
        timestamp_token.record(self.name, "timestamp", self.timestamp)

    def handle_contact(self, data_store, line_number, tokens, datafile, change_id):
        """Handles a general contact message
        :param data_store: The data store that this is importing into
        :param line_number: The number of the line currently being processed
        :param tokens: The tokens parsed from the line being processed
        :param datafile: The datafile being imported
        :param change_id: The ID representing this import as a change
        """
        bearing_token = tokens[4]
        contact_id_token = tokens[5]
        speed_token = tokens[6]
        date_token = tokens[9]
        time_token = tokens[10]
        lat_token = tokens[15]
        lat_hem_token = tokens[16]
        lon_token = tokens[17]
        lon_hem_token = tokens[18]
        # TODO - figure out which one is the range
        # TODO - figure out which sensor the contact comes from

        timestamp = self.parse_timestamp(date_token.text, time_token.text)
        contact_timestamp_token = combine_tokens(date_token, time_token)
        contact_timestamp_token.record(self.name, "timestamp", timestamp)

        detecting_platform = self.get_cached_platform(data_store, self.platform_name, change_id)
        detecting_sensor = self.get_cached_sensor(
            data_store,
            sensor_name="Wecdis-General-Contact",  # TODO - figure out the general contact sensor
            sensor_type="Wecdis",
            platform_id=detecting_platform.platform_id,
            change_id=change_id,
        )
        contact = datafile.create_contact(
            data_store=data_store,
            platform=detecting_platform,
            sensor=detecting_sensor,
            timestamp=timestamp,
            parser_name=self.short_name,
        )

        contact.track_number = contact_id_token.text
        contact_id_token.record(self.name, "track number", contact.track_number)

        bearing_valid, bearing = convert_absolute_angle(
            bearing_token.text, line_number, self.errors, self.error_type
        )
        if bearing_valid:
            contact.bearing = bearing
            bearing_token.record(self.name, "bearing", bearing)

        speed_valid, speed = convert_speed(
            speed_token.text, unit_registry.knots, line_number, self.errors, self.error_type
        )
        if speed_valid:
            contact.soa = speed  # Assuming that WECDIS records speed of approach
            speed_token.record(self.name, "speed", speed)

        # TODO - There is almost certainly a range (probably [13]), confirm
        # range_valid, range =

        location = self._parse_lat_lon_tokens(lat_token, lat_hem_token, lon_token, lon_hem_token)
        if location:
            contact.location = location

        if location:
            contact.location = location
            combine_tokens(lat_token, lon_token).record(
                self.name, "location", contact.location, "DMS"
            )

    def handle_position(self, data_store, line_number, tokens, datafile, change_id):
        """Handles the position information for ownship
        :param data_store: The data store that this is importing into
        :param line_number: The number of the line currently being processed
        :param tokens: The tokens parsed from the line being processed
        :param datafile: The datafile being imported
        :param change_id: The ID representing this import as a change
        """
        lat_token = tokens[3]
        lat_hem_token = tokens[4]
        lon_token = tokens[5]
        lon_hem_token = tokens[6]
        heading_token = tokens[7]
        speed_token = tokens[8]

        platform = self.get_cached_platform(data_store, self.platform_name, change_id=change_id)
        sensor = self.get_cached_sensor(
            data_store=data_store,
            sensor_name="",
            sensor_type=None,
            platform_id=platform.platform_id,
            change_id=change_id,
        )

        state = datafile.create_state(data_store, platform, sensor, self.timestamp, self.short_name)

        location = self._parse_lat_lon_tokens(lat_token, lat_hem_token, lon_token, lon_hem_token)
        if location:
            state.location = location

        combine_tokens(lat_token, lon_token).record(self.name, "location", location, "DMS")

        heading_valid, heading = convert_absolute_angle(
            heading_token.text, line_number, self.errors, self.error_type
        )
        if heading_valid:
            state.heading = heading
            heading_token.record(self.name, "heading", heading)

        speed_valid, speed = convert_speed(
            speed_token.text, unit_registry.knots, line_number, self.errors, self.error_type
        )
        if speed_valid:
            state.speed = speed
            speed_token.record(self.name, "speed", speed)

    def handle_tma(self, data_store, line_number, tokens, datafile, change_id):
        """Handles a contact generated from Target Motion Analysis (TMA)
        :param data_store: The data store that this is importing into
        :param line_number: The number of the line currently being processed
        :param tokens: The tokens parsed from the line being processed
        :param datafile: The datafile being imported
        :param change_id: The ID representing this import as a change
        """
        # As per MWC's REP parser, only handle the BRG messages
        type_token = tokens[2]
        if type_token.text != "BRG":
            return

        date_token = tokens[5]
        time_token = tokens[6]
        bearing_token = tokens[7]
        course_token = tokens[9]  # Optional
        lat_token = tokens[11]
        lat_hem_token = tokens[12]
        lon_token = tokens[13]
        lon_hem_token = tokens[14]
        tma_name_token = tokens[21]

        # TODO - work out speed/range fields
        timestamp = self.parse_timestamp(date_token.text, time_token.text)
        contact_timestamp_token = combine_tokens(date_token, time_token)
        contact_timestamp_token.record(self.name, "timestamp", timestamp)

        detecting_platform = self.get_cached_platform(data_store, self.platform_name, change_id)
        detecting_sensor = self.get_cached_sensor(
            data_store,
            sensor_name="Wecdis-TMA",  # TODO - confirm name for this sensor
            sensor_type="TMA",
            platform_id=detecting_platform.platform_id,
            change_id=change_id,
        )
        contact = datafile.create_contact(
            data_store=data_store,
            platform=detecting_platform,
            sensor=detecting_sensor,
            timestamp=timestamp,
            parser_name=self.short_name,
        )

        location = self._parse_lat_lon_tokens(lat_token, lat_hem_token, lon_token, lon_hem_token)
        if location:
            contact.location = location

        contact.track_number, _, _ = tma_name_token.text.partition("*")
        tma_name_token.record(self.name, "track number", contact.track_number)

        bearing_valid, bearing = convert_absolute_angle(
            bearing_token.text, line_number, self.errors, self.error_type
        )
        if bearing_valid:
            contact.bearing = bearing
            bearing_token.record(self.name, "bearing", bearing)

        if course_token.text:
            course_valid, course = convert_absolute_angle(
                course_token.text, line_number, self.errors, self.error_type
            )
            if course_valid:
                contact.orientation = course
                course_token.record(self.name, "bearing", course)

    # TODO - find out what the TTM range/bearing combinations relate to (a/b)

    def _parse_lat_lon_tokens(self, lat_token, lat_hem_token, lon_token, lon_hem_token):
        """Parse latitude and longitude tokens as a location"""

        latitude = lat_token.text
        longitude = lon_token.text

        if not latitude or not longitude:
            return None

        location = Location(
            errors=self.errors,
            error_type=self.error_type,
        )

        if not location.set_latitude_dms(
            degrees=latitude[:2], minutes=latitude[2:], seconds=0, hemisphere=lat_hem_token.text
        ):
            return None

        if not location.set_longitude_dms(
            degrees=longitude[:3],
            minutes=longitude[3:],
            seconds=0,
            hemisphere=lon_hem_token.text,
        ):
            return None

        return location

    @staticmethod
    def parse_timestamp(date, time):
        if len(date) == 6:
            format_str = "%y%m%d"
        else:
            format_str = "%Y%m%d"

        if len(time) == 6:
            format_str += "%H%M%S"
        else:
            format_str += "%H%M%S.%f"

        try:
            parsed_timestamp = datetime.strptime(date + time, format_str)
        except ValueError:
            return None

        return parsed_timestamp

    # TODO - do we need to parse the TZS to get the time zone?
