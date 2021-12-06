import math
from datetime import datetime

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.sqlalchemy_utils import get_lowest_privacy
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed

DELETE = "eUM_DELETE"


class FullShoreImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Full Shore Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Full Shore Importer",
            datafile_type="Full Shore",
            default_privacy="Private",
        )
        self.platform = None

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".CSV"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("RECORD#,REC_DATE,REC_TIME")

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line_number == 1:
            # Skip the header
            return

        tokens = line.tokens(line.CSV_TOKENISER, ",")

        # Date time parsing common to both file formats
        date_token = tokens[1]
        time_token = tokens[2]
        timestamp = self.parse_timestamp(tokens[1].text, tokens[2].text)
        combine_tokens(date_token, time_token).record(self.name, "timestamp", timestamp)

        operation_token = tokens[3]
        if operation_token.text == DELETE:
            return  # We're ignoring deletions

        id_token = tokens[9]
        source_token = tokens[10]

        if source_token.text == "OWN_SHIP":
            # Ask for the platform & hold onto it
            self.platform = self.get_cached_platform(
                data_store, platform_name=None, change_id=change_id
            )

        sensor_type = data_store.add_to_sensor_types(source_token.text, change_id).name
        privacy = get_lowest_privacy(data_store)
        # The data we've got indicates that Ownship is always first, so this should be ok
        sensor = self.platform.get_sensor(
            data_store=data_store,
            sensor_name=source_token.text,
            sensor_type=sensor_type,
            privacy=privacy,
            change_id=change_id,
        )

        state = datafile.create_state(data_store, self.platform, sensor, timestamp, self.short_name)

        # The positions of many tokens vary between two formats
        if len(tokens) == 1933:
            # If we've got a sure value use that one, otherwise use the uncertain one
            lat_token = tokens[1225] if tokens[1225].text else tokens[1272]
            lon_token = tokens[1226] if tokens[1226].text else tokens[1273]
            course_token = tokens[1231] if tokens[1231].text else tokens[1266]
            speed_token = tokens[1232] if tokens[1232].text else tokens[1267]
            depth_token = tokens[1227] if tokens[1227].text else tokens[1274]
            if tokens[1474].text:
                name_p1_token = tokens[1474]
                name_p2_token = tokens[1464]
            else:
                name_p1_token = tokens[1483]
                name_p2_token = tokens[10]
        elif len(tokens) == 1986:
            pass
        else:
            # Invalid line length (based on the files we've got so far...)
            self.errors.append(
                {
                    self.error_type: f"Error on line {line_number}. Unable to read Full Shore with {len(tokens)} tokens"
                }
            )
            return

        location = Location(errors=self.errors, error_type=self.error_type)
        lat_degs = float(lat_token.text) * (180 / math.pi)
        lon_degs = float(lon_token.text) * (180 / math.pi)
        lat_success = location.set_latitude_decimal_degrees(lat_degs)
        lon_success = location.set_longitude_decimal_degrees(lon_degs)
        if lat_success and lon_success:
            state.location = location
            combine_tokens(lat_token, lon_token).record(
                self.name, "location", state.location, "decimal degrees"
            )

        elevation_valid, elevation = convert_distance(
            depth_token.text, unit_registry.meter, line_number, self.errors, self.error_type
        )
        if elevation_valid:
            state.elevation = elevation * -1
            depth_token.record(self.name, "altitude", state.elevation)

        heading_valid, heading = convert_absolute_angle(
            course_token.text, line_number, self.errors, self.error_type
        )
        if heading_valid:
            state.heading = heading
            course_token.record(self.name, "heading", heading)

        speed_valid, speed = convert_speed(
            speed_token.text, unit_registry.knot, line_number, self.errors, self.error_type
        )

        datafile.flush_extracted_tokens()

    @staticmethod
    def parse_timestamp(date, time):
        """Parses the fullshore timestamp from a date & time string
        :param date: The date part of the timestamp
        :type date: String
        :param time: The time part of the timestamp
        :type time: String
        :return a datetime (GMT/UTC/Zulu) if conversion successful
            or None if unsuccessful
        :rtype: datetime | None
        """
        timestamp_format = "%d/%m/%Y %H:%M:%S"
        timestamp_string = f"{date} {time}"
        try:
            res = datetime.strptime(timestamp_string, timestamp_format)
        except ValueError:
            return None
        return res

    # TODO:
    # - Platform / sensor (will need to ask for platform)
    # - Determine which of the file formats we've actually got
    # Will need to check the data to see if there is a difference in length
    # Otherwise, will need to get column names
    # - Read in ownship positions
    # - Read in tracks/contacts

    # Some complexities:
    # - We have two different formatted files (Sept 20 / Jan 21 formatted one way, Mar 21 formatted differently)
    # - Full Shore format has a range of different sources of data, with any
    # being present on a row (but only one present per row) so ownship tracks
    # are mixed up with contacts
    #    - To minimise possible issues with classification of importer,
    #    check if ownship and then parse everything else as contacts
    # - There are a lot of columns in these data files, with lots of the important
    # ones being towards the end of the table. This may cause issues with the
    # hightlighting.
