from .importer import Importer
from datetime import datetime

from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed
from pepys_import.file.highlighter.support.combine import combine_tokens


class NMEAImporter(Importer):
    name = "NMEA File Format Importer"

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

    def load_this_file(self, data_store, path, file_object, datafile):
        print("NMEA parser working on " + path)

        for line_number, line in enumerate(file_object.lines()):
            tokens = line.tokens()
            if len(tokens) > 0:

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
                    combine_tokens(date_token, time_token).record(
                        self.name, "timestamp", timestamp, "n/a"
                    )

                    state = datafile.create_state(sensor, timestamp)
                    location = self.parse_location(
                        self.latitude,
                        self.latitude_hem,
                        self.longitude,
                        self.longitude_hem,
                    )
                    state.location = location
                    combine_tokens(lat_token, lon_token).record(
                        self.name, "location", location, "DMS"
                    )

                    heading = convert_absolute_angle(self.heading, line_number)
                    if heading:
                        state.heading = heading
                    heading_token.record(self.name, "heading", heading, "degrees")

                    speed = convert_speed(self.speed, line_number)
                    if speed:
                        state.speed = speed
                    speed_token.record(self.name, "speed", speed, "knots")

                    state.privacy = privacy.privacy_id

                    self.date = None
                    self.time = None
                    self.speed = None
                    self.heading = None
                    self.latitude = None

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
    def parse_location(lat, lat_hem, lon, long_hem):
        lat_degrees = float(lat[0:2])
        lat_minutes = float(lat[2:4])
        lat_seconds = float(lat[4:])
        lat_degrees = lat_degrees + lat_minutes / 60 + lat_seconds / 60 / 60

        lon_degrees = float(lon[0:3])
        lon_minutes = float(lon[3:5])
        lon_seconds = float(lon[5:])
        lon_degrees = lon_degrees + lon_minutes / 60 + lon_seconds / 60 / 60

        if lat_hem == "S":
            lat_degrees = -1 * lat_degrees

        if long_hem == "W":
            lon_degrees = -1 * lon_degrees

        return f"({lat_degrees} {lon_degrees})"

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
