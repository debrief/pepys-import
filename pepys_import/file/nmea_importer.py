from .importer import Importer
from datetime import datetime

from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants


class NMEAImporter(Importer):
    name = "NMEA File Format Importer"
    validation_level = constants.BASIC_LEVEL
    short_name = "NMEA Importer"

    def __init__(self, separator=","):
        super().__init__()
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

    def tokens(self, line):
        """
        Tokenize parsed line.

        :return: A series of Token object from this line of text, separated according to
         the FieldSeparator specified by this importer.
        """
        if self.separator == " ":
            return line.split()
        else:
            return line.split(self.separator)

    # TODO: does nothing now
    def record(self, importer, record_type, measurement_object) -> None:
        """
        Log the fact that this set of characters was loaded by the specified importer.
        After the intermediate objects have been imported into the database,
        it is possible to modify the import record to include a URL to a browser-based
        view of that imported row.

        :param importer: Name of the import library that loaded this line
        :type importer: String
        :param record_type: Description of the type of data that was loaded
        :type record_type: String
        :param measurement_object: Intermediate object for the line that was imported.
        :type measurement_object: Measurement
        :return: Nothing
        """

    def load_this_file(self, data_store, path, file_contents, datafile):
        print("NMEA parser working on " + path)
        error_type = self.short_name + f" - Parsing error on {path}"
        prev_location = None
        datafile.measurements[self.short_name] = list()
        for line_number, line in enumerate(file_contents):
            if line_number > 5000:
                break
            tokens = self.tokens(line)
            if len(tokens) > 0:

                msg_type = tokens[1]
                if msg_type == "DZA":
                    self.date = tokens[2]
                    self.time = tokens[3]
                elif msg_type == "VEL":
                    self.speed = tokens[6]
                elif msg_type == "HDG":
                    self.heading = tokens[2]
                elif msg_type == "POS":
                    self.latitude = tokens[3]
                    self.latitude_hem = tokens[4]
                    self.longitude = tokens[5]
                    self.longitude_hem = tokens[6]

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
                        platform_name=None,
                        platform_type="Ferry",
                        nationality="FR",
                        privacy="Public",
                    )
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

                    state = datafile.create_state(sensor, timestamp)

                    self.latitude = Location(
                        *self.parse_location(self.latitude, self.latitude_hem)
                    )
                    if not self.latitude.parse():
                        self.errors.append(
                            {
                                error_type: f"Line {line_number}. Error in latitude parsing"
                            }
                        )
                        continue

                    self.longitude = Location(
                        *self.parse_location(self.longitude, self.longitude_hem)
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
                    if heading:
                        state.heading = heading

                    speed = convert_speed(
                        self.speed, line_number, self.errors, error_type
                    )
                    if speed:
                        state.speed = speed

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
    def parse_location(location, hemisphere):
        return location[:2], location[2:4], location[4:], hemisphere

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
