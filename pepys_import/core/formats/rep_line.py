from datetime import datetime
from .location import Location
from . import unit_registry


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


class REPLine:
    def __init__(self, line_number, line):
        self.line_num = line_number
        self.line = line

        self.timestamp = None
        self.vessel = None
        self.symbology = None
        self.latitude = None
        self.longitude = None
        self.heading = None
        self.speed = None
        self.depth = None
        self.text_label = None

        # Initialize pint's unit registry object
        self.unit_registry = unit_registry

    def print(self):
        print(
            "REP Line {} - Timestamp: {} Vessel: {} Symbology: {} Latitude: {} "
            "Longitude: {} Heading: {} Speed: {} Depth: {} TextLabel: {}".format(
                self.line_num,
                self.timestamp,
                self.vessel,
                self.symbology,
                self.latitude,
                self.longitude,
                self.heading,
                self.speed,
                self.depth,
                self.text_label,
            )
        )

    def parse(self):

        tokens = self.line.split()

        if len(tokens) < 15:
            print(
                "Error on line {} not enough tokens: {}".format(
                    self.line_num, self.line
                )
            )
            return False

        # separate token strings
        date_token = tokens[0]
        time_token = tokens[1]
        vessel_name_token = tokens[2]
        symbology_token = tokens[3]
        lat_degrees_token = tokens[4]
        lat_mins_token = tokens[5]
        lat_secs_token = tokens[6]
        lat_hemi_token = tokens[7]
        long_degrees_token = tokens[8]
        long_mins_token = tokens[9]
        long_secs_token = tokens[10]
        long_hemi_token = tokens[11]
        heading_token = tokens[12]
        speed_token = tokens[13]
        depth_token = tokens[14]

        if len(tokens) >= 16:
            self.text_label = " ".join(tokens[15:])

        if len(date_token) != 6 and len(date_token) != 8:
            print(
                f"Line {self.line_num}. Error in Date format {date_token}. "
                f"Should be either 2 of 4 figure date, followed by month then date"
            )
            return False

        # Times always in Zulu/GMT
        if len(time_token) != 6 and len(time_token) != 10:
            print(
                f"Line {self.line_num}. Error in Time format {time_token}. "
                f"Should be HHMMSS[.SSS]"
            )
            return False

        self.timestamp = parse_timestamp(date_token, time_token)

        self.vessel = vessel_name_token.strip('"')

        symbology_values = symbology_token.split("[")
        if len(symbology_values) >= 1:
            if len(symbology_values[0]) != 2 and len(symbology_values[0]) != 5:
                print(
                    f"Line {self.line_num}. Error in Symbology format "
                    f"{symbology_token}. Should be 2 or 5 chars"
                )
                return False
        if len(symbology_values) != 1 and len(symbology_values) != 2:
            print(f"Line {self.line_num}. Error in Symbology format {symbology_token}")
            return False

        self.symbology = symbology_token

        self.latitude = Location(
            lat_degrees_token, lat_mins_token, lat_secs_token, lat_hemi_token
        )
        if not self.latitude.parse():
            print(f"Line {self.line_num}. Error in latitude parsing")
            return False

        self.longitude = Location(
            long_degrees_token, long_mins_token, long_secs_token, long_hemi_token
        )
        if not self.longitude.parse():
            print(f"Line {self.line_num}. Error in longitude parsing")
            return False

        try:
            valid_heading = float(heading_token)
        except ValueError:
            print(
                f"Line {self.line_num}. Error in heading value {heading_token}. "
                f"Couldn't convert to a number"
            )
            return False
        if 0.0 > valid_heading or valid_heading >= 360.0:
            print(
                f"Line {self.line_num}. Error in heading value {heading_token}. "
                f"Should be be between 0 and 359.9 degrees"
            )
            return False

        # Set heading as degree(quantity-with-unit) object
        self.heading = valid_heading * self.unit_registry.degree

        try:
            valid_speed = float(speed_token)
        except ValueError:
            print(
                f"Line {self.line_num}. Error in speed value {speed_token}. "
                f"Couldn't convert to a number"
            )
            return False

        # Set speed as knots(quantity-with-unit) object
        self.speed = valid_speed * self.unit_registry.knot

        try:
            if depth_token == "NaN":
                self.depth = 0.0
            else:
                self.depth = float(depth_token)
        except ValueError:
            print(
                f"Line {self.line_num}. Error in depth value {depth_token}. "
                f"Couldn't convert to a number"
            )
            return False

        return True

    def get_platform(self):
        return self.vessel

    def get_location(self):
        return f"POINT({self.longitude} {self.latitude})"
