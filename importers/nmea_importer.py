from datetime import datetime
from prompt_toolkit.shortcuts.progress_bar import ProgressBar

from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


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

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # keep track of generated platform name
        platform_name = None

        with ProgressBar() as pb:
            for line_number, line in enumerate(pb(file_object.lines()), 1):
                tokens = line.tokens(line.CSV_DELIM, ",")

                if len(tokens) > 1:

                    msg_type = tokens[1].text
                    if msg_type == "DZA":
                        self.date_token = tokens[2]
                        self.date = self.date_token.text
                        self.time_token = tokens[3]
                        self.time = self.time_token.text
                    elif msg_type == "VEL":
                        self.speed_token = tokens[6]
                        self.speed = self.speed_token.text
                    elif msg_type == "HDG":
                        self.heading_token = tokens[2]
                        self.heading = self.heading_token.text
                    elif msg_type == "POS":
                        self.latitude = tokens[3].text
                        self.latitude_hem = tokens[4].text
                        self.lat_token = combine_tokens(tokens[3], tokens[4])
                        self.longitude = tokens[5].text
                        self.longitude_hem = tokens[6].text
                        self.lon_token = combine_tokens(tokens[5], tokens[6])

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
                            change_id=change_id,
                        )
                        # capture the name
                        platform_name = platform.name
                        sensor_type = data_store.add_to_sensor_types(
                            "_GPS", change_id=change_id
                        )
                        privacy = data_store.missing_data_resolver.resolve_privacy(
                            data_store, change_id
                        )
                        sensor = platform.get_sensor(
                            data_store=data_store,
                            sensor_name=platform.name,
                            sensor_type=sensor_type,
                            privacy=privacy.name,
                            change_id=change_id,
                        )
                        timestamp = self.parse_timestamp(self.date, self.time)
                        combine_tokens(self.date_token, self.time_token).record(
                            self.name, "timestamp", timestamp, "n/a"
                        )

                        state = datafile.create_state(
                            data_store, platform, sensor, timestamp, self.short_name
                        )

                        self.location = Location(
                            errors=self.errors, error_type=self.error_type,
                        )

                        if not self.location.set_latitude_dms(
                            degrees=self.latitude[:2],
                            minutes=self.latitude[2:],
                            seconds=0,
                            hemisphere=self.latitude_hem,
                        ):
                            continue

                        if not self.location.set_longitude_dms(
                            degrees=self.longitude[:3],
                            minutes=self.longitude[3:],
                            seconds=0,
                            hemisphere=self.longitude_hem,
                        ):
                            continue

                        if platform_name in self.prev_location:
                            state.prev_location = self.prev_location[platform_name]

                        state.location = self.location
                        self.prev_location[platform_name] = state.location

                        combine_tokens(self.lat_token, self.lon_token).record(
                            self.name, "location", state.location, "DMS"
                        )

                        heading = convert_absolute_angle(
                            self.heading, line_number, self.errors, self.error_type
                        )
                        if heading:
                            state.heading = heading
                        self.heading_token.record(
                            self.name, "heading", heading, "degrees"
                        )

                        speed = convert_speed(
                            self.speed,
                            unit_registry.knots,
                            line_number,
                            self.errors,
                            self.error_type,
                        )
                        if speed:
                            state.speed = speed
                        self.speed_token.record(self.name, "speed", speed, "knots")

                        state.privacy = privacy.privacy_id

                        self.date = None
                        self.time = None
                        self.speed = None
                        self.heading = None
                        self.latitude = None
                        self.latitude_hem = None
                        self.longitude = None
                        self.longitude_hem = None
                        self.location = None

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
