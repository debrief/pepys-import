from datetime import datetime
from enum import Enum

from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle


class MsgType(Enum):
    TIME = "DZM"
    PLATFORM = "VNM"
    CONTACT = "CONTACT"
    POSITION = "CPOS"


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
        return ["CHART", "VER"] in file_contents

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):

        tokens = line.tokens(line.CSV_TOKENISER, ",")

        if len(tokens) > 1:
            # Always skip the $POSL tag [0]
            msg_type = tokens[1].text
            if msg_type == MsgType.PLATFORM:
                self.handle_vnm(tokens, line_number)
            elif msg_type == MsgType.TIME:
                self.handle_dza(tokens, line_number)
            elif msg_type == MsgType.CONTACT:
                self.handle_contact(data_store, line_number, tokens, datafile, change_id)

        # Do we have all the information we need?
        if (
            self.platform_name
            and self.timestamp
            and self.speed
            and self.heading
            and self.latitude
            and self.latitude_hemisphere
            and self.longitude
            and self.longitude_hemisphere
        ):
            platform = self.get_cached_platform(data_store, self.platform_name, change_id=change_id)
            sensor = self.get_cached_sensor(
                data_store=data_store,
                sensor_name="",
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

            state = datafile.create_state(
                data_store, platform, sensor, self.timestamp, self.short_name
            )

            self.location = Location(
                errors=self.errors,
                error_type=self.error_type,
            )

            if not self.location.set_latitude_dms(
                degrees=self.latitude[:2],
                minutes=self.latitude[2:],
                seconds=0,
                hemisphere=self.latitude_hem,
            ):
                return

            if not self.location.set_longitude_dms(
                degrees=self.longitude[:3],
                minutes=self.longitude[3:],
                seconds=0,
                hemisphere=self.longitude_hem,
            ):
                return

            state.location = self.location

            combine_tokens(self.lat_token, self.lon_token).record(
                self.name, "location", state.location, "DMS"
            )

            heading_valid, heading = convert_absolute_angle(
                self.heading, line_number, self.errors, self.error_type
            )
            if heading_valid:
                state.heading = heading
                self.heading_token.record(self.name, "heading", heading)

        datafile.flush_extracted_tokens()

    def handle_vnm(self, vnm_tokens, line_number):
        """Extracts the important information from a VNM line
        :param vnm_tokens: A tokenised VNM line
        :ptype vnm_tokens: Line (list of tokens)"""
        if len(vnm_tokens) < 3:
            self.errors.append(
                {
                    self.error_type: f"Line {line_number} does not contain enough parts. No platform name in {vnm_tokens}"
                }
            )
            return  # Not necessarily an error, but can't do anything with it now
        if vnm_tokens[1].text != "VNM":
            # Programming error, shouldn't be hit but if it does we're passing the wrong line
            raise TypeError(f"Expected a VNM line, given {vnm_tokens[1].text}")
        # Ignore the *XX part if present
        self.platform_name, _, _ = vnm_tokens[2].text.partition("*")

    def handle_dza(self, dza_tokens, line_number):
        """Extracts the important information from a DZA (Timestamp) line
        :param dza_tokens: A tokenised DZA line
        :ptype dza_tokens: Line (list of tokens)"""
        if len(dza_tokens) < 4:
            self.errors.append(
                {
                    self.error_type: f"Line {line_number} does not contain enough parts. No timestamp provided."
                }
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

        combined_token = combine_tokens(dza_tokens[2], dza_tokens[3])
        combined_token.record(self.name, "timestamp", self.timestamp)

    def handle_contact(self, data_store, line_number, tokens, datafile, change_id):
        # bearing_token = tokens[4]
        # contact_id_token = tokens[5]
        # speed_token = tokens[6]
        date_token = tokens[9]
        time_token = tokens[10]
        # lat_token = tokens[15]
        # lat_hem_token = tokens[16]
        # lon_token = tokens[17]
        # lon_hem_token = tokens[18]
        # TODO - figure out which one is the range
        # TODO - figure out which sensor the contact comes from

        timestamp = self.parse_timestamp(date_token.text, time_token.text)

        detecting_platform = self.get_cached_platform(data_store, self.platform_name, change_id)
        detecting_sensor = self.get_cached_sensor(
            data_store,
            sensor_name=None,
            sensor_type=None,
            platform_id=detecting_platform.platform_id,
            change_id=change_id,
        )
        contact = datafile.create_contact(
            data_store=data_store,
            platform=detecting_platform,
            sensor=detecting_sensor,
            timestamp=timestamp,
            parser_name=self.name,
        )
        print(contact)

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
            return False

        return parsed_timestamp
