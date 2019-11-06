from datetime import datetime
from .location import Location
from . import unit_registry, quantity


class State:
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
            "REP Line {} - Timestamp: {} Vessel: {} Symbology: {} Latitude: {} Longitude: {} Heading: {} Speed: {} Depth: {} TextLabel: {}".format(
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
        text_label_token = ""

        if len(tokens) >= 16:
            # TODO: join back into single string, or extract full substring
            self.text_label = tokens[15:]

        if len(date_token) != 6 and len(date_token) != 8:
            print(
                "Line {}. Error in Date format {}. Should be either 2 of 4 figure date, followed by month then date".format(
                    self.line_num, date_token
                )
            )
            return False

        # Times always in Zulu/GMT
        if len(time_token) != 6 and len(time_token) != 10:
            print(
                "Line {}. Error in Time format {}. Should be HHMMSS[.SSS]".format(
                    self.line_num, time_token
                )
            )
            return False

        self.timestamp = self.parse_timestamp(date_token, time_token)

        self.vessel = vessel_name_token.strip('"')

        symbology_values = symbology_token.split("[")
        if len(symbology_values) >= 1:
            if len(symbology_values[0]) != 2 and len(symbology_values[0]) != 5:
                print(
                    "Line {}. Error in Symbology format {}. Should be 2 or 5 chars".format(
                        self.line_num, symbology_token
                    )
                )
                return False
        if len(symbology_values) != 1 and len(symbology_values) != 2:
            print(
                "Line {}. Error in Symbology format {}".format(
                    self.line_num, symbology_token
                )
            )
            return False

        self.symbology = symbology_token

        self.latitude = Location(
            lat_degrees_token, lat_mins_token, lat_secs_token, lat_hemi_token
        )
        if not self.latitude.parse():
            print("Line {}. Error in latitude parsing".format(self.line_num))
            return False

        self.longitude = Location(
            long_degrees_token, long_mins_token, long_secs_token, long_hemi_token
        )
        if not self.latitude.parse():
            print("Line {}. Error in longitude parsing".format(self.line_num))
            return False

        try:
            valid_heading = float(heading_token)
        except ValueError:
            print(
                "Line {}. Error in heading value {}. Couldn't convert to a number".format(
                    self.line_num, heading_token
                )
            )
            return False
        if 0.0 > valid_heading >= 360.0:
            print(
                "Line {}. Error in heading value {}. Should be be between 0 and 359.9 degrees".format(
                    self.line_num, heading_token
                )
            )
            return False

        # Set heading as degree(quantity-with-unit) object
        self.set_heading(valid_heading * self.unit_registry.degree)

        try:
            valid_speed = float(speed_token)
        except ValueError:
            print(
                "Line {}. Error in speed value {}. Couldn't convert to a number".format(
                    self.line_num, speed_token
                )
            )
            return False

        # Set speed as knots(quantity-with-unit) object
        self.set_speed(valid_speed * self.unit_registry.knot)

        try:
            if depth_token == "NaN":
                self.depth = 0.0
            else:
                self.depth = float(depth_token)
        except ValueError:
            print(
                "Line {}. Error in depth value {}. Couldn't convert to a number".format(
                    self.line_num, depth_token
                )
            )
            return False

        return True

    def parse_timestamp(self, date, time):
        if len(date) == 6:
            formatStr = "%y%m%d"
        else:
            formatStr = "%Y%m%d"

        if len(time) == 6:
            formatStr += "%H%M%S"
        else:
            formatStr += "%H%M%S.%f"

        return datetime.strptime(date + time, formatStr)

    def set_speed(self, speed):
        self.speed = speed

    def set_heading(self, heading: quantity):
        self.heading = heading

    def set_latitude(self):
        pass

    def set_longitude(self):
        pass

    def get_line_number(self):
        return self.line_num

    def get_timestamp(self):
        return self.timestamp

    def get_platform(self):
        return self.vessel

    def get_symbology(self):
        return self.symbology

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_heading(self):
        return self.heading

    def get_speed(self):
        return self.speed

    def get_depth(self):
        return self.depth

    def get_text_label(self):
        return self.text_label
