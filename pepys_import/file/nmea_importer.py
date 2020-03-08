from .importer import Importer
from datetime import datetime

from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants


class NMEAImporter(Importer):
    def __init__(
        self,
        name="NMEA File Format Importer",
        validation_level=constants.BASIC_LEVEL,
        short_name="NMEA Importer",
        separator=",",
    ):
        super().__init__(name, validation_level, short_name)
        self.separator = separator
        self.errors = list()

        self.latitude = None
        self.latitude_hem = None
        self.longitude = None
        self.longitude_hem = None
        self.date = None
        self.time = None
        self.heading = None
        self.speed = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return "$POSL" in first_line

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_object, datafile):
        self.errors = list()
        print("NMEA parser working on " + path)
        error_type = self.short_name + f" - Parsing error on {path}"
        prev_location = None
        datafile.measurements[self.short_name] = list()
        # keep track of generated platform name
        platform_name = None

        for line_number, line in enumerate(file_object.lines()):
            tokens = line.tokens(line.CSV_DELIM, ",")

            if len(tokens) > 1:

                msg_type = tokens[1].text
                if msg_type == "DZA":
                    date_token = tokens[2]
                    self.date = date_token.text
                    time_token = tokens[3]
                    self.time = time_token.text
                elif msg_type == "VEL":
                    speed_token = tokens[6]
                    self.speed = speed_token.text
                elif msg_type == "HDG":
                    heading_token = tokens[2]
                    self.heading = heading_token.text
                elif msg_type == "POS":
                    self.latitude = tokens[3].text
                    self.latitude_hem = tokens[4].text
                    lat_token = combine_tokens(tokens[3], tokens[4])
                    self.longitude = tokens[5].text
                    self.longitude_hem = tokens[6].text
                    lon_token = combine_tokens(tokens[5], tokens[6])

                # do we have all we need?
                if (
                    self.date
                    and self.time
                    and self.speed
                    and self.heading
                    and self.latitude
                    and self.latitude_hem
                    and self.longitude
                    and self.longitude_hem
                ):

                    # and finally store it
                    platform = data_store.get_platform(
                        platform_name=platform_name,
                        platform_type="Ferry",
                        nationality="FR",
                        privacy="Public",
                    )
                    # capture the name
                    platform_name = platform.name
                    sensor_type = data_store.add_to_sensor_types("_GPS")
                    privacy = data_store.missing_data_resolver.resolve_privacy(
                        data_store
                    )
                    sensor = platform.get_sensor(
                        data_store=data_store,
                        sensor_name=platform.name,
                        sensor_type=sensor_type,
                        privacy=privacy.name,
                    )
                    timestamp = self.parse_timestamp(self.date, self.time)
                    combine_tokens(date_token, time_token).record(
                        self.name, "timestamp", timestamp, "n/a"
                    )

                    state = datafile.create_state(sensor, timestamp, self.short_name)

                    if not isinstance(self.latitude, Location):
                        self.latitude = Location(
                            degrees=self.latitude[:2],
                            minutes=self.latitude[2:],
                            seconds=0,
                            hemisphere=self.latitude_hem,
                            errors=self.errors,
                            error_type=error_type,
                        )
                    if not self.latitude.parse():
                        self.errors.append(
                            {
                                error_type: f"Line {line_number}. Error in latitude parsing"
                            }
                        )
                        continue
                    if not isinstance(self.longitude, Location):
                        self.longitude = Location(
                            degrees=self.longitude[:3],
                            minutes=self.longitude[3:],
                            seconds=0,
                            hemisphere=self.longitude_hem,
                            errors=self.errors,
                            error_type=error_type,
                        )
                    if not self.longitude.parse():
                        self.errors.append(
                            {
                                error_type: f"Line {line_number}. Error in longitude parsing"
                            }
                        )
                        continue

                    state.prev_location = prev_location
                    state.location = f"POINT({self.longitude.as_degrees()} {self.latitude.as_degrees()})"
                    prev_location = state.location

                    heading = convert_absolute_angle(
                        self.heading, line_number, self.errors, error_type
                    )
                    state.location = state.location
                    combine_tokens(lat_token, lon_token).record(
                        self.name, "location", state.location, "DMS"
                    )

                    heading = convert_absolute_angle(
                        self.heading, line_number, self.errors, error_type
                    )
                    if heading:
                        state.heading = heading.to(unit_registry.radians).magnitude
                    heading_token.record(self.name, "heading", heading, "degrees")

                    speed = convert_speed(
                        self.speed, line_number, self.errors, error_type
                    )
                    if speed:
                        state.speed = speed
                    speed_token.record(self.name, "speed", speed, "knots")

                    state.privacy = privacy.privacy_id

                    self.date = None
                    self.time = None
                    self.speed = None
                    self.heading = None
                    self.latitude = None
                    self.latitude_hem = None
                    self.longitude = None
                    self.longitude_hem = None

    # def requires_user_review(self) -> bool:
    #     """
    #     Whether this importer requires user review of the loaded intermediate data
    #     before pushing to the database.  The review may be by viewing an HTML import
    #     summary, or examining some statistical/graphical overview.
    #
    #     :return: True or False
    #     :rtype: bool
    #     """
    #     pass

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

        return datetime.strptime(date + time, format_str)
