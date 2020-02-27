from .importer import Importer
from datetime import datetime

from pepys_import.utils.unit_utils import convert_heading, convert_speed
from ..core.formats.location import Location


class NMEAImporter(Importer):
    name = "NMEA File Format Importer"
    validation_level = "basic"

    def __init__(self, separator=","):
        super().__init__()
        self.separator = separator

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
                    and self.longitude
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
                    lat_degrees, lat_minutes, lat_seconds = (
                        self.latitude[0:2],
                        self.latitude[2:4],
                        self.latitude[4:],
                    )
                    latitude = Location(
                        lat_degrees, lat_minutes, lat_seconds, self.latitude_hem
                    )
                    if not latitude.parse():
                        print(f"Line {line_number}. Error in latitude parsing")
                        return False

                    lon_degrees, lon_minutes, lon_seconds = (
                        self.longitude[0:2],
                        self.longitude[2:4],
                        self.longitude[4:],
                    )
                    longitude = Location(
                        lon_degrees, lon_minutes, lon_seconds, self.longitude_hem
                    )
                    if not longitude.parse():
                        print(f"Line {line_number}. Error in longitude parsing")
                        return False

                    state.location = (
                        f"POINT({longitude.as_degrees()} {latitude.as_degrees()})"
                    )

                    heading = convert_heading(self.heading, line_number)
                    if heading:
                        state.heading = heading

                    speed = convert_speed(self.speed, line_number)
                    if speed:
                        state.speed = speed

                    state.privacy = privacy.privacy_id

                    self.date = None
                    self.time = None
                    self.speed = None
                    self.heading = None
                    self.latitude = None
                    self.longitude = None

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
