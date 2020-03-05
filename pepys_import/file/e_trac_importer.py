from .importer import Importer
from datetime import datetime
from pepys_import.core.formats import unit_registry
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed
from pepys_import.file.highlighter.support.combine import combine_tokens


class ETracImporter(Importer):
    name = "E-Trac Format Importer"

    def __init__(self, separator=" "):
        super().__init__()
        self.separator = separator
        self.text_label = None
        self.depth = 0.0

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return first_line.startswith("!Target,MMSI")

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_object, datafile):
        print("E-trac parser working on ", path)

        for line_number, line in enumerate(file_object.lines(), 1):
            # Skip the header
            if line_number == 1:
                continue

            tokens = line.tokens(line.CSV_DELIM, ",")
            if len(tokens) <= 1:
                # the last line may be empty, don't worry
                continue
            elif len(tokens) < 17:
                print(
                    "Error on line {} not enough tokens: {}".format(line_number, line),
                    len(tokens),
                )
                continue

            # separate token strings
            date_token = tokens[2]
            time_token = tokens[3]
            lat_degrees_token = tokens[4]
            long_degrees_token = tokens[5]
            heading_token = tokens[8]
            speed_token = tokens[6]
            comp_name_token = tokens[18]
            vessel_name = self.name_for(comp_name_token.text)

            if len(date_token.text) != 10:
                print(len(date_token.text))
                print(
                    f"Line {line_number}. Error in Date format '{date_token.text}'. Should be 10 figure data"
                )
                continue

            # Times always in Zulu/GMT
            if len(time_token.text) != 8:
                print(
                    f"Line {line_number}. Error in Date format {time_token.text}. Should be HH:mm:ss"
                )
                continue

            timestamp = self.parse_timestamp(date_token.text, time_token.text)

            timestamp_combined_token = combine_tokens(date_token, time_token)
            timestamp_combined_token.record(self.name, "timestamp", timestamp, "n/a")

            # and finally store it
            platform = data_store.get_platform(
                platform_name=vessel_name,
                nationality="UK",
                platform_type="Fisher",
                privacy="Public",
            )
            sensor_type = data_store.add_to_sensor_types("GPS")
            privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name="E-Trac",
                sensor_type=sensor_type,
                privacy=privacy.name,
            )
            state = datafile.create_state(sensor, timestamp)
            state.privacy = privacy.privacy_id

            state.location = (
                f"POINT({long_degrees_token.text} {lat_degrees_token.text})"
            )

            # TODO: Depth is currently set to a constant value of 0.0
            # Do we need to parse this from the file?
            state.elevation = -1 * self.depth

            heading = convert_absolute_angle(heading_token.text, line_number)
            state.heading = heading.to(unit_registry.radians).magnitude

            speed = convert_speed(speed_token.text, line_number)
            state.speed = speed

    @staticmethod
    def name_for(token):
        # split into two
        tokens = token.split()
        return tokens[1]

    @staticmethod
    def parse_timestamp(date, time):
        format_str = "%Y/%m/%d "
        format_str += "%H:%M:%S"

        res = datetime.strptime(date.strip() + " " + time.strip(), format_str)

        return res
