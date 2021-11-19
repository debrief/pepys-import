from datetime import datetime
from enum import Enum

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed


class MsgType(str, Enum):
    """The supported WECDIS message types"""

    TIME = "DZA"
    PLATFORM = "VNM"
    CONTACT = "CONTACT"
    POSITION = "POS"  # Could be CPOS, POS, POS1, POS2, ... POSN
    TMA = "TMA"
    DEPTH = "PDS"
    TTM = "TTM"  # Could be TTM1, TTM2, TTM3


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
        self.elevation = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return "$POSL" in header

    def can_load_this_file(self, file_contents):
        # Need to differentiate from general NMEA - so check charts/version available
        contents_string = " ".join(file_contents[0:100])
        return "VER" in contents_string and "CHART" in contents_string

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):

        tokens = line.tokens(line.CSV_TOKENISER, ",")
        if len(tokens) > 1:
            # Always skip the $POSL tag [0]
            msg_type = tokens[1].text.upper().strip()
            if msg_type == MsgType.PLATFORM:
                self.handle_vnm(tokens, line_number)
            elif msg_type == MsgType.TIME:
                self.handle_timestamp(tokens, line_number)
            elif msg_type == MsgType.DEPTH:
                self.handle_depth(tokens, line_number)
            elif msg_type == MsgType.CONTACT:
                self.handle_contact(data_store, line_number, tokens, datafile, change_id)
            elif MsgType.POSITION in msg_type:
                # Do we have all the information we need?
                if self.platform_name and self.timestamp:
                    self.handle_position(data_store, line_number, tokens, datafile, change_id)
            elif msg_type == MsgType.TMA:
                self.handle_tma(data_store, line_number, tokens, datafile, change_id)
            elif MsgType.TTM in msg_type:
                self.handle_ttm(data_store, line_number, tokens, datafile, change_id)
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

    def handle_depth(self, tokens, line_number):
        """Extracts the depth from the PDS line
        :param tokens: A tokenised PDS line
        :ptype tokens: Line (list of tokens)"""
        depth_token = tokens[2]
        depth_units_token = tokens[3]  # This is an assumption about the unit being position 3
        if depth_token and depth_token.text:
            # Making an assumption of how this would look if using FT.
            # [3] may not be the units but unclear from a single sample file
            unit_text, _, _ = depth_units_token.text.upper().partition("*")
            units = unit_registry.foot if unit_text == "FT" else unit_registry.meter
            depth_valid, depth = convert_distance(
                depth_token.text, units, line_number, self.errors, self.error_type
            )
            if depth_valid:
                self.elevation = -1 * depth
            depth_token.record(self.name, "Depth", self.elevation)

    def handle_timestamp(self, dza_tokens, line_number):
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
            sensor_name="Wecdis",  # TODO - figure out the general contact sensor
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
        source_token = tokens[1]
        sensor_token = tokens[2]
        lat_token = tokens[3]
        lat_hem_token = tokens[4]
        lon_token = tokens[5]
        lon_hem_token = tokens[6]
        sensor_name = f"{source_token.text}_{sensor_token.text}"
        combine_tokens(source_token, sensor_token).record(self.name, "sensor", sensor_name)

        platform = self.get_cached_platform(data_store, self.platform_name, change_id=change_id)
        sensor = self.get_cached_sensor(
            data_store=data_store,
            sensor_name=f"{sensor_name}",
            sensor_type=sensor_token.text,
            platform_id=platform.platform_id,
            change_id=change_id,
        )

        state = datafile.create_state(data_store, platform, sensor, self.timestamp, self.short_name)

        location = self._parse_lat_lon_tokens(lat_token, lat_hem_token, lon_token, lon_hem_token)
        if location:
            state.location = location

        combine_tokens(lat_token, lon_token).record(self.name, "location", location, "DMS")

        if tokens[1].text == "CPOS":
            heading_token = tokens[7]
            speed_token = tokens[8]
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

        if self.elevation:
            state.elevation = self.elevation

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

        sensor_name_token = tokens[4]
        date_token = tokens[5]
        time_token = tokens[6]
        bearing_token = tokens[7]
        course_token = tokens[9]  # Optional

        # TMA lines seem to have two possible lengths - 21 or 22 tokens
        # The extra token sits just before the latitude
        if len(tokens) == 21:
            lat_token = tokens[10]
            lat_hem_token = tokens[11]
            lon_token = tokens[12]
            lon_hem_token = tokens[13]
            tma_name_token = tokens[20]
        elif len(tokens) == 22:
            lat_token = tokens[11]
            lat_hem_token = tokens[12]
            lon_token = tokens[13]
            lon_hem_token = tokens[14]
            tma_name_token = tokens[21]

        # TODO - work out speed/range fields
        timestamp = self.parse_timestamp(date_token.text, time_token.text)
        contact_timestamp_token = combine_tokens(date_token, time_token)
        contact_timestamp_token.record(self.name, "timestamp", timestamp)

        sensor_name = sensor_name_token.text
        sensor_name_token.record(self.name, "sensor", sensor_name)
        detecting_platform = self.get_cached_platform(data_store, self.platform_name, change_id)
        detecting_sensor = self.get_cached_sensor(
            data_store,
            sensor_name=f"TMA-{sensor_name}",
            sensor_type=f"{sensor_name}",
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
                course_token.record(self.name, "course", course)

    def handle_ttm(self, data_store, line_number, tokens, datafile, change_id):
        """Handles TTM sensor contacts
        :param data_store: The data store that this is importing into
        :param line_number: The number of the line currently being processed
        :param tokens: The tokens parsed from the line being processed
        :param datafile: The datafile being imported
        :param change_id: The ID representing this import as a change
        """
        # There are two sensors
        sensor_token = tokens[2]
        range_a_token = tokens[3]
        bearing_a_token = tokens[4]
        range_b_token = tokens[6]
        bearing_b_token = tokens[7]
        lat_token = tokens[17]
        lat_hem_token = tokens[18]
        lon_token = tokens[19]
        lon_hem_token = tokens[20]

        sensor_name = sensor_token.text
        sensor_token.record(self.name, "sensor", sensor_name)
        detecting_platform = self.get_cached_platform(data_store, self.platform_name, change_id)

        contact_a = self.generate_ttm_contact(
            sensor_name + "_a",
            data_store,
            datafile,
            line_number,
            detecting_platform,
            range_a_token,
            bearing_a_token,
            change_id,
        )
        contact_b = self.generate_ttm_contact(
            sensor_name + "_b",
            data_store,
            datafile,
            line_number,
            detecting_platform,
            range_b_token,
            bearing_b_token,
            change_id,
        )

        location = self._parse_lat_lon_tokens(lat_token, lat_hem_token, lon_token, lon_hem_token)
        if location:
            contact_a.location = location
            contact_b.location = location

        contact_a.track_number = f"TTM_{sensor_name}_a"
        contact_b.track_number = f"TTM_{sensor_name}_b"

    def generate_ttm_contact(
        self,
        sensor_name,
        data_store,
        datafile,
        line_number,
        detecting_platform,
        range_token,
        bearing_token,
        change_id,
    ):
        """Generates a contact from a TTM sensor range/bearing
        TTM has two ranges and bearings - appearing to come from two linked sources
        :param sensor_name: The name of the sensor that we're generating this contact from
        :param data_store: The data store that this is importing into
        :param datafile: The datafile being imported
        :param line_number: The number of the line currently being processed
        :param detecting_platform: The platform that's detecting the contact
        :param range_token: The token giving the range of the contact
        :param bearing_token: The token giving the bearing of the contact
        :param change_id: The ID representing this import as a change
        """
        detecting_sensor = self.get_cached_sensor(
            data_store,
            sensor_name=f"TTM-{sensor_name}",
            sensor_type=f"{sensor_name}",
            platform_id=detecting_platform.platform_id,
            change_id=change_id,
        )
        contact = datafile.create_contact(
            data_store=data_store,
            platform=detecting_platform,
            sensor=detecting_sensor,
            timestamp=self.timestamp,  # This contact type doesn't have its own timestamp
            parser_name=self.short_name,
        )

        bearing_valid, bearing = convert_absolute_angle(
            bearing_token.text, line_number, self.errors, self.error_type
        )
        if bearing_valid:
            contact.bearing = bearing
            bearing_token.record(self.name, "bearing", bearing)

        range_valid, contact_range = convert_distance(
            range_token.text,
            unit_registry.kilometers,  # TODO - confirm whether units are km, kyds or NM
            line_number,
            self.errors,
            self.error_type,
        )
        if range_valid:
            contact.range = contact_range
            range_token.record(self.name, "range", contact_range)

        return contact

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
