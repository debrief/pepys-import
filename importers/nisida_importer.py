from pepys_import.file.highlighter.level import HighlightLevel
import sys
from datetime import datetime

import geopy
import geopy.distance

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import CANCEL_IMPORT, Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

# This regex matches anything that isn't a slash, or the empty string between two slashes
# See:
# https://stackoverflow.com/questions/62600563/regex-to-match-entries-between-slashes-but-not-slashes-including-empty-entrie
# for some discussion
SLASH_TOKENISER = r"[^/]+|(?<=/)(?=/)"

SENSOR_CODE_TO_NAME = {
    "RDR": "Radar",
    "PSON": "Passive Sonar",
    "ASON": "Active Sonar",
    "VDS": "Variable Depth Sonar",
    "HSON": "Helo Sonar",
    "HRDR": "Helo Radar",
    "TAS": "Array Sonar",
    "VIS": "Visible",
    "IR": "Infrared",
    "OTHER": "Generic",
}

POS_SOURCE_TO_NAME = {"GPS": "GPS", "DR": "Dead Recknoning", "IN": "Inertial"}


class NisidaImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Nisida Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Nisida Importer",
            datafile_type="Nisida",
        )
        self.current_line_no = None
        self.last_entry_with_text = None
        self.month = None
        self.year = None
        self.platform = None

        self.set_highlighting_level(HighlightLevel.DATABASE)

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("UNIT/")

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        self.current_line_no = line_number

        if line.text.startswith("UNIT/"):
            # Handle UNIT line giving month, year and platform
            # Format is:
            # UNIT/ADRI/OCT03/SRF/
            tokens = line.tokens(SLASH_TOKENISER)

            if len(tokens) < 4:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Not enough tokens in UNIT/ line: {line.text}"
                    }
                )
                return CANCEL_IMPORT

            if self.not_missing(tokens[1].text):
                platform_name = tokens[1].text
            else:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Missing platform name in UNIT/ line: {line.text}"
                    }
                )
                return CANCEL_IMPORT

            tokens[1].record(self.name, "platform", platform_name)
            self.platform = self.get_cached_platform(
                data_store, platform_name=platform_name, change_id=change_id
            )

            try:
                month_and_year = datetime.strptime(tokens[2].text, "%b%y")
                self.month = month_and_year.month
                self.year = month_and_year.year
                tokens[2].record(self.name, "month and year", month_and_year.strftime("%Y-%m"))
            except (ValueError, AttributeError):
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Invalid month/year in UNIT/ line: {line.text}"
                    }
                )
                return CANCEL_IMPORT

        elif line.text.startswith("//"):
            # This is a continuation of the previous line, so add whatever else is in this line
            # to the content field of the previous entry
            if self.last_entry_with_text is None:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Line continuation not immediately after valid line: {line.text}"
                    }
                )
                return

            if line.text.endswith("/"):
                text_to_add = line.text[2:-1]
            else:
                text_to_add = line.text[2:]
            if isinstance(self.last_entry_with_text, data_store.db_classes.Comment):
                self.last_entry_with_text.content = self.last_entry_with_text.content + text_to_add
            else:
                self.last_entry_with_text.remarks = self.last_entry_with_text.remarks + text_to_add
            line.record(self.name, "comment text", text_to_add)
            datafile.flush_extracted_tokens()
        elif len(line.text) > 7 and line.text[7] == "/" and line.text[0:5].isdigit():
            # Check whether line starts with something like "311206Z/" (a timestamp and a slash)
            # Checking like this is faster than using regular expressions on each line

            # Reset last_entry_with_text, so that if continuation characters aren't directly
            # after an entry we processed, then we will raise an error rather than
            # add to the incorrect entry
            self.last_entry_with_text = None

            # Split line by slash
            self.tokens = line.tokens(SLASH_TOKENISER)

            self.timestamp = self.parse_timestamp(self.tokens[0])
            self.tokens[0].record(self.name, "timestamp", self.timestamp)

            self.tokens[1].record(self.name, "message type", self.tokens[1].text)

            try:
                if self.tokens[1].text.upper() in ("NAR", "COC"):
                    # The COC and NAR messages have the same format
                    # COC isn't actually described in the documentation for the format,
                    # but seems to be Commanding Officer Comments, and is present in the example
                    self.process_narrative(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() == "DET":
                    self.process_detection(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() == "ATT":
                    self.process_attack(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() in ("DIP", "SSQ"):
                    self.process_dip_or_buoy(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() == "EXP":
                    self.process_mastexposure(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() == "SEN":
                    self.process_sensor(data_store, datafile, change_id)
                elif self.tokens[1].text.upper() == "ENV":
                    self.process_enviroment(data_store, datafile, change_id)
                elif len(self.tokens) >= 4:
                    if self.tokens[3].text in POS_SOURCE_TO_NAME.keys():
                        self.process_position(data_store, datafile, change_id)
                else:
                    self.errors.append(
                        {
                            self.error_type: f"Error on line {self.current_line_no}. "
                            f"Line does not match any known message format: {line.text}"
                        }
                    )
                    return
            except Exception as e:  # pragma: no cover (catches any other error, but all errors we can test are already caught elsewhere)
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"General error processing line - exception was: '{e}' on code line {sys.exc_info()[-1].tb_lineno}: {line.text}"
                    }
                )
                return
            datafile.flush_extracted_tokens()
        else:
            # Not a line we recognise, so just skip to next one
            return

    def not_missing(self, text):
        empty = text == ""
        missing = text == "-"

        return not (empty or missing)

    def parse_timestamp(self, timestamp_token):
        timestamp_text = timestamp_token.text

        if timestamp_text[-1] != "Z":
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid format for timestamp - missing Z character: {timestamp_text}"
                }
            )
            return False

        # Note: No need to wrap this in a try-catch to check for parsing errors
        # as the timestamp_text is already guaranteed to consist of 6 digits
        # as an if statement checks that around Line 135, before this function
        # is called
        day = int(timestamp_text[0:2])
        hour = int(timestamp_text[2:4])
        minute = int(timestamp_text[4:6])

        try:
            timestamp = datetime(
                year=self.year, month=self.month, day=day, hour=hour, minute=minute
            )
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid timestamp: {timestamp_text}"
                }
            )
            return False
        return timestamp

    def parse_lat_lon_strings(self, lat_str, lon_str):
        # The latitude and longitude values are given in degrees and decimal minutes as follows:
        # (D)DDMM.MMH
        try:
            lat_hemisphere = lat_str[-1]
            lon_hemisphere = lon_str[-1]

            lat_minutes = float(lat_str[-6:-1])
            lon_minutes = float(lon_str[-6:-1])

            lat_degrees = float(lat_str[:-6])
            lon_degrees = float(lon_str[:-6])
        except (ValueError, IndexError):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Unable to parse latitude/longitude values: {lat_str}, {lon_str}"
                }
            )
            return False

        loc = Location(errors=self.errors, error_type=self.error_type)
        valid_lat = loc.set_latitude_dms(lat_degrees, lat_minutes, 0, lat_hemisphere)
        valid_lon = loc.set_longitude_dms(lon_degrees, lon_minutes, 0, lon_hemisphere)

        if valid_lat and valid_lon:
            return loc
        else:
            return False

    def parse_time(self, text):
        splitted = text.split(":")

        try:
            hour = int(splitted[0])
            mins = int(splitted[1])
        except (ValueError, AttributeError, IndexError):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Unable to parse time value to float: {text}"
                }
            )
            return False

        try:
            # Take current timestamp value, and replace the hours and mins, and zero the seconds
            new_timestamp = self.timestamp.replace(hour=hour, minute=mins, second=0)
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid time value: {text}"
                }
            )
            return False

        return new_timestamp

    def location_plus_range_and_bearing(self, orig_loc, bearing, range_value):
        # Get starting point from the orig_loc Location object
        start = geopy.Point(orig_loc.latitude, orig_loc.longitude)

        # Convert distance to kilometres and initialise object
        range_in_km = range_value.to(unit_registry.kilometre)
        d = geopy.distance.distance(kilometers=range_in_km.magnitude)

        # Use the `destination` method with the bearing
        result = d.destination(point=start, bearing=bearing.magnitude)

        result_loc = Location()
        result_loc.set_latitude_decimal_degrees(result.latitude)
        result_loc.set_longitude_decimal_degrees(result.longitude)

        return result_loc

    def comment_text_from_whole_line(self):
        """Extracts the text of the whole line excluding the initial timestamp entry
        and records it as comment text"""
        comment_text = "/".join([t.text for t in self.tokens[1:]])
        combine_tokens(*self.tokens[1:]).record(self.name, "comment text", comment_text)

        return comment_text

    def process_narrative(self, data_store, datafile, change_id):
        comment_text = self.tokens[2].text
        self.tokens[2].record(self.name, "comment text", comment_text)

        if self.tokens[1].text == "NAR":
            comment_type = data_store.add_to_comment_types("Narrative", change_id)
        elif self.tokens[1].text == "COC":
            comment_type = data_store.add_to_comment_types("CO Comments", change_id)

        comment = datafile.create_comment(
            data_store=data_store,
            platform=self.platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_entry_with_text = comment

    def process_position(self, data_store, datafile, change_id):
        pos_source_token = self.tokens[3]
        pos_source = self.parse_pos_source(pos_source_token)
        # No need to check if pos_source returns none, as we only
        # call this function if self.tokens[3] is in the POS_SOURCE_TO_NAME dict
        # and therefore this function is guaranteed to succeed

        sensor_type = data_store.add_to_sensor_types(pos_source, change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=pos_source,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        state = datafile.create_state(
            data_store, self.platform, sensor, self.timestamp, self.short_name
        )

        lat_token = self.tokens[1]
        lon_token = self.tokens[2]

        loc = self.parse_location(lat_token, lon_token)

        if loc:
            state.location = loc

        course_token = self.tokens[4]
        speed_token = self.tokens[5]
        depth_token = self.tokens[6]

        if self.not_missing(course_token.text):
            course_valid, course = convert_absolute_angle(
                course_token.text, self.current_line_no, self.errors, self.error_type
            )
            if course_valid:
                state.course = course
                course_token.record(self.name, "course", course)

        if self.not_missing(speed_token.text):
            speed_valid, speed = convert_speed(
                speed_token.text,
                unit_registry.knots,
                self.current_line_no,
                self.errors,
                self.error_type,
            )
            if speed_valid:
                state.speed = speed
                speed_token.record(self.name, "speed", speed)

        if self.not_missing(depth_token.text):
            elevation_valid, elevation = convert_distance(
                depth_token.text,
                unit_registry.metre,
                self.current_line_no,
                self.errors,
                self.error_type,
            )
            if elevation_valid:
                state.elevation = elevation * -1
                depth_token.record(self.name, "depth", state.elevation)

    def process_detection(self, data_store, datafile, change_id):
        # Get the sensor code, as we need it to create the sensor object
        sensor_code_token = self.tokens[2]
        sensor_name = SENSOR_CODE_TO_NAME.get(sensor_code_token.text)
        if sensor_name is None:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid sensor code: {sensor_code_token.text}"
                }
            )
            return
        sensor_code_token.record(self.name, "sensor", sensor_name)

        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=sensor_name,
            change_id=change_id,
        )

        # Create the contact object that we're going to add to the database
        contact = datafile.create_contact(
            data_store=data_store,
            platform=self.platform,
            sensor=sensor,
            timestamp=self.timestamp,
            parser_name=self.short_name,
        )

        # Parse the bearing field
        bearing_token = self.tokens[3]
        bearing_valid = False
        if self.not_missing(bearing_token.text):
            bearing_valid, bearing = convert_absolute_angle(
                bearing_token.text, self.current_line_no, self.errors, self.error_type
            )
            if bearing_valid:
                contact.bearing = bearing
                bearing_token.record(self.name, "bearing", bearing)

        # Parse the range field
        range_token = self.tokens[4]
        range_valid = False
        if self.not_missing(range_token.text):
            range_valid, range_value = convert_distance(
                range_token.text,
                unit_registry.nautical_mile,
                self.current_line_no,
                self.errors,
                self.error_type,
            )
            if range_valid:
                contact.range = range_value
                range_token.record(self.name, "range", range_value)

        # Parse the track number field
        track_number_token = self.tokens[5]
        if self.not_missing(track_number_token.text):
            contact.track_number = track_number_token.text
            track_number_token.record(self.name, "track number", contact.track_number)

        # Parse lat and lon for own location
        lat_token = self.tokens[6]
        lon_token = self.tokens[7]

        loc = self.parse_location(lat_token, lon_token)
        if loc is None:
            return

        # Parse position source
        pos_source_token = self.tokens[8]
        pos_source = self.parse_pos_source(pos_source_token)
        if pos_source is None:
            return

        # Parse remarks
        remarks_token = self.tokens[9]
        if self.not_missing(remarks_token):
            contact.remarks = remarks_token.text
            remarks_token.record(self.name, "remarks", remarks_token.text)

        self.last_entry_with_text = contact

        # Create a State entry for the own position values, with a sensor of Position Source
        sensor_type = data_store.add_to_sensor_types(pos_source, change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=pos_source,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        state = datafile.create_state(
            data_store, self.platform, sensor, self.timestamp, self.short_name
        )

        if loc:
            state.location = loc

        # Create a geometry entry for the position given by 'own position' plus the range and bearing
        geom_type_obj = data_store.add_to_geometry_types("Tactical", change_id=change_id)
        geom_sub_type_id = data_store.add_to_geometry_sub_types(
            "Detection", geom_type_obj.name, change_id=change_id
        ).geo_sub_type_id

        if (not bearing_valid) or (not range_valid) or (not loc):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Not enough data to calculate attack position - bearing, range or own location missing"
                }
            )
            return

        geometry_location = self.location_plus_range_and_bearing(loc, bearing, range_value)

        datafile.create_geometry(
            data_store=data_store,
            geom=geometry_location,
            geom_type_id=geom_type_obj.geo_type_id,
            geom_sub_type_id=geom_sub_type_id,
            parser_name=self.short_name,
        )

    def process_attack(self, data_store, datafile, change_id):
        # Parse the bearing field
        bearing_token = self.tokens[3]
        bearing_valid = False
        if self.not_missing(bearing_token.text):
            bearing_valid, bearing = convert_absolute_angle(
                bearing_token.text, self.current_line_no, self.errors, self.error_type
            )
            if bearing_valid:
                bearing_token.record(self.name, "bearing", bearing)

        # Parse the range field
        range_token = self.tokens[4]
        range_valid = False
        if self.not_missing(range_token.text):
            range_valid, range_value = convert_distance(
                range_token.text,
                unit_registry.nautical_mile,
                self.current_line_no,
                self.errors,
                self.error_type,
            )
            if range_valid:
                range_token.record(self.name, "range", range_value)

        # Parse lat and lon for own location
        lat_token = self.tokens[6]
        lon_token = self.tokens[7]

        loc = self.parse_location(lat_token, lon_token)
        if loc is None:
            return

        # Parse position source
        pos_source_token = self.tokens[8]
        pos_source = self.parse_pos_source(pos_source_token)
        if pos_source is None:
            return

        # Create a State entry for the own position values, with a sensor of Position Source
        sensor_type = data_store.add_to_sensor_types(pos_source, change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=pos_source,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )
        state = datafile.create_state(
            data_store, self.platform, sensor, self.timestamp, self.short_name
        )

        state.location = loc

        # Create a geometry entry for the position given by 'own position' plus the range and bearing
        geom_type_obj = data_store.add_to_geometry_types("Tactical", change_id=change_id)
        geom_sub_type_id = data_store.add_to_geometry_sub_types(
            "Attack", geom_type_obj.name, change_id=change_id
        ).geo_sub_type_id

        if (not bearing_valid) or (not range_valid) or (not loc):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Not enough data to calculate attack position - bearing, range or own location missing"
                }
            )
            return

        geometry_location = self.location_plus_range_and_bearing(loc, bearing, range_value)

        datafile.create_geometry(
            data_store=data_store,
            geom=geometry_location,
            geom_type_id=geom_type_obj.geo_type_id,
            geom_sub_type_id=geom_sub_type_id,
            parser_name=self.short_name,
        )

        comment_type = data_store.add_to_comment_types("Attack", change_id)

        comment_text = self.comment_text_from_whole_line()

        comment = datafile.create_comment(
            data_store=data_store,
            platform=self.platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_entry_with_text = comment

    def process_dip_or_buoy(self, data_store, datafile, change_id):
        # Parse lat and lon for own location
        lat_token = self.tokens[5]
        lon_token = self.tokens[6]

        loc = self.parse_location(lat_token, lon_token)
        if loc is None:
            return

        # Get type of message - Dip (type DIP) or Buoy (type SSQ)
        message_type = self.tokens[1].text

        message_name_from_message_type_field = {"DIP": "Dip", "SSQ": "Buoy"}

        # Create a geometry entry for the position given
        geom_type_obj = data_store.add_to_geometry_types("Tactical", change_id=change_id)
        geom_sub_type_id = data_store.add_to_geometry_sub_types(
            message_name_from_message_type_field[message_type],
            geom_type_obj.name,
            change_id=change_id,
        ).geo_sub_type_id

        datafile.create_geometry(
            data_store=data_store,
            geom=loc,
            geom_type_id=geom_type_obj.geo_type_id,
            geom_sub_type_id=geom_sub_type_id,
            parser_name=self.short_name,
        )

        comment_type = data_store.add_to_comment_types(
            message_name_from_message_type_field[message_type], change_id
        )

        comment_text = self.comment_text_from_whole_line()

        comment = datafile.create_comment(
            data_store=data_store,
            platform=self.platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_entry_with_text = comment

    def process_mastexposure(self, data_store, datafile, change_id):
        mast_type_token = self.tokens[2]
        mast_type = mast_type_token.text
        mast_type_token.record(self.name, "mast type", mast_type)

        sensor_type = data_store.add_to_sensor_types(mast_type, change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=mast_type,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )

        time_up = None
        time_down = None
        if self.not_missing(self.tokens[3].text):
            time_up = self.parse_time(self.tokens[3].text)
            if time_up:
                self.tokens[3].record(self.name, "time up", time_up)
            else:
                # Parsing error already raised inside self.parse_time function
                return

        if self.not_missing(self.tokens[4].text):
            time_down = self.parse_time(self.tokens[4].text)
            if time_down:
                self.tokens[4].record(self.name, "time down", time_down)
            else:
                return

        if (not time_up) and (not time_down):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"You must provide at least one of time up or time down {self.tokens[3].text} {self.tokens[4].text}"
                }
            )
            return

        activation = datafile.create_activation(
            data_store=data_store,
            sensor=sensor,
            start=time_up,
            end=time_down,
            parser_name=self.short_name,
        )

        activation.remarks = self.tokens[5].text
        self.tokens[5].record(self.name, "remarks", self.tokens[5].text)

        self.last_entry_with_text = activation

    def process_sensor(self, data_store, datafile, change_id):
        sensor_code_token = self.tokens[2]
        sensor_name = SENSOR_CODE_TO_NAME.get(sensor_code_token.text)
        if sensor_name is None:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid sensor code: {sensor_code_token.text}"
                }
            )
            return
        sensor_code_token.record(self.name, "Sensor", sensor_name)

        sensor_type = data_store.add_to_sensor_types(sensor_name, change_id=change_id).name
        privacy = get_lowest_privacy(data_store)
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=sensor_name,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )

        time_on = None
        time_off = None

        if self.not_missing(self.tokens[3].text):
            time_on = self.parse_time(self.tokens[3].text)
            if time_on:
                self.tokens[3].record(self.name, "time on", time_on)
            else:
                # Parsing error already raised inside self.parse_time function
                return

        if self.not_missing(self.tokens[4].text):
            time_off = self.parse_time(self.tokens[4].text)
            if time_off:
                self.tokens[4].record(self.name, "time off", time_off)
            else:
                return

        if (not time_off) and (not time_on):
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"You must provide at least one of time on or time off {self.tokens[3].text} {self.tokens[4].text}"
                }
            )
            return

        activation = datafile.create_activation(
            data_store=data_store,
            sensor=sensor,
            start=time_on,
            end=time_off,
            parser_name=self.short_name,
        )

        activation.remarks = self.tokens[5].text
        self.tokens[5].record(self.name, "remarks", self.tokens[5].text)

        self.last_entry_with_text = activation

    def process_enviroment(self, data_store, datafile, change_id):
        comment_type = data_store.add_to_comment_types("Environment", change_id)

        comment_text = self.comment_text_from_whole_line()

        comment = datafile.create_comment(
            data_store=data_store,
            platform=self.platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_entry_with_text = comment

    def parse_pos_source(self, pos_source_token):
        if self.not_missing(pos_source_token):
            pos_source = POS_SOURCE_TO_NAME.get(pos_source_token.text)
            if pos_source is None:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Invalid position source value: {pos_source_token.text}"
                    }
                )
                return
            pos_source_token.record(self.name, "position source", pos_source)

            return pos_source

    def parse_location(self, lat_token, lon_token):
        if self.not_missing(lat_token) and self.not_missing(lon_token):
            loc = self.parse_lat_lon_strings(lat_token.text, lon_token.text)

            if not loc:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Cannot parse latitude/longitude location: {lat_token.text} {lon_token.text}"
                    }
                )
                return

            combine_tokens(lat_token, lon_token).record(
                self.name, "location", loc, "degrees and decimal minutes"
            )

        return loc
