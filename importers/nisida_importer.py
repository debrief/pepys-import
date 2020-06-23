from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

SLASH_SPLIT_REGEX = r"(.*?)(?:/|$)"


class NisidaImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Nisida Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Nisida Importer",
        )
        self.current_line_no = None
        self.last_comment_entry = None
        self.month = None
        self.year = None
        self.platform = None

    def can_load_this_type(self, suffix):
        return True

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        for line in file_contents:
            if line.startswith("UNIT/"):
                return True
        return False

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        self.current_line_no = line_number

        if line.text.startswith("UNIT/"):
            # Handle UNIT line giving month, year and platform
            # Format is:
            # UNIT/ADRI/OCT03/SRF/
            tokens = line.tokens(SLASH_SPLIT_REGEX)

            platform_name = tokens[1].text
            tokens[1].record(self.name, "platform", platform_name)
            self.platform = data_store.get_platform(
                platform_name=platform_name, change_id=change_id,
            )

            month_and_year = datetime.strptime(tokens[2].text, "%b%y")
            self.month = month_and_year.month
            self.year = month_and_year.year
            tokens[2].record(self.name, "month and year", month_and_year.strftime("%Y-%m"))
        elif line.text.startswith("//"):
            # This is a continuation of the previous line, so add whatever else is in this line
            # to the content field of the previous entry
            print(f"Processing continuation with text {line.text}")

            if self.last_comment_entry is None:
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
            self.last_comment_entry.content = self.last_comment_entry.content + text_to_add
            line.record(self.name, "comment text", text_to_add)
        elif len(line.text) > 7 and line.text[7] == "/" and line.text[0:5].isdigit():
            # Check whether line starts with something like "311206Z/" (a timestamp and a slash)
            # Checking like this is faster than using regular expressions on each line

            # Reset last_comment_entry, so that if continuation characters aren't directly
            # after an entry we processed, then we will raise an error rather than
            # add to the incorrect entry
            self.last_comment_entry = None

            # Split line by slash
            self.tokens = line.tokens(SLASH_SPLIT_REGEX)

            self.timestamp = self.parse_timestamp(self.tokens[0])
            self.tokens[0].record(self.name, "timestamp", self.timestamp)

            # breakpoint()
            print([t.text for t in self.tokens])

            if self.tokens[1].text.upper() in ("NAR", "COC"):
                self.process_narrative(data_store, datafile, change_id)
            elif self.tokens[1].text.upper() == "DET":
                pass
            elif self.tokens[1].text.upper() == "ATT":
                pass
            elif self.tokens[1].text.upper() == "DIP":
                pass
            elif self.tokens[1].text.upper() == "SSQ":
                pass
            elif self.tokens[1].text.upper() == "EXP":
                pass
            elif self.tokens[1].text.upper() == "SEN":
                pass
            elif self.tokens[1].text.upper() == "ENV":
                pass
            elif len(self.tokens) >= 3 and self.tokens[3].text in ("GPS", "DR", "IN"):
                print("Processing position")
                self.process_position(data_store, datafile, change_id)
            else:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Line does not match any known message format: {line.text}"
                    }
                )
                return
        else:
            # Not a line we recognise, so just skip to next one
            return

    def not_missing(self, text):
        empty = text == ""
        missing = text == "-"

        if empty:
            print("Found empty field")

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

        try:
            day = int(timestamp_text[0:2])
            hour = int(timestamp_text[2:4])
            minute = int(timestamp_text[4:6])
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid format for timestamp - day, hour or min could not be converted to float: {timestamp_text}"
                }
            )
            return False

        return datetime(year=self.year, month=self.month, day=day, hour=hour, minute=minute)

    def parse_location(self, lat_token, lon_token):
        # The latitude and longitude values are given in degrees and decimal minutes as follows:
        # (D)DDMM.MMH
        try:
            lat_hemisphere = lat_token.text[-1]
            lon_hemisphere = lon_token.text[-1]

            lat_minutes = float(lat_token.text[-6:-1])
            lon_minutes = float(lon_token.text[-6:-1])

            lat_degrees = float(lat_token.text[:-6])
            lon_degrees = float(lon_token.text[:-6])
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Unable to parse latitude/longitude values: {lat_token.text}, {lon_token.text}"
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

    def process_narrative(self, data_store, datafile, change_id):
        comment_text = self.tokens[2].text
        self.tokens[2].record(self.name, "comment text", comment_text)

        comment_type = data_store.add_to_comment_types("Narrative", change_id)

        comment = datafile.create_comment(
            data_store=data_store,
            platform=self.platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_comment_entry = comment

    def process_position(self, data_store, datafile, change_id):
        pos_source_token = self.tokens[3]

        if pos_source_token.text == "GPS":
            pos_source = "GPS"
        elif pos_source_token.text == "DR":
            pos_source = "Dead Reckoning"
        elif pos_source_token.text == "IN":
            pos_source = "Inertial"
        else:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid position source value: {pos_source_token.text}"
                }
            )
            return
        pos_source_token.record(self.name, "position source", pos_source)

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
            combine_tokens(lat_token, lon_token).record(
                self.name, "location", loc, "decimal degrees"
            )

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
