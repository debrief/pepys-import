from .core_parser import CoreParser
from pepys_import.core.formats.state2 import State2
from datetime import datetime
from pepys_import.core.formats.location import Location
from pepys_import.core.formats import unit_registry, quantity


class ETracParser(CoreParser):
    def __init__(self):
        super().__init__("E-Trac File Format")

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".TXT"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return first_line.startswith("!Target,MMSI")

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents, data_file_id):
        print("E-trac parser working on ", path)
        line_num = 0
        for line in file_contents:

            line_num += 1

            # skip first line
            if line_num == 1:
                continue

            tokens = line.split(",")
            if len(tokens) < 17:
                print("Error on line {} not enough tokens: {}".format(line_num, line))
                return False

            # separate token strings
            mmsi_token = tokens[1]
            date_token = tokens[2]
            time_token = tokens[3]
            lat_degrees_token = tokens[4]
            long_degrees_token = tokens[5]
            heading_token = tokens[8]
            speed_token = tokens[6]
            comp_name_token = tokens[18]

            if len(date_token) != 12:
                print(len(date_token))
                print(
                    "Line {}. Error in Date format {}. Should be 10 figure data".format(
                        line_num, date_token
                    )
                )
                return False

            # Times always in Zulu/GMT
            if len(time_token) != 8:
                print(
                    "Line {}. Error in Time format {}. Should be HH:mm:ss".format(
                        line_num, time_token
                    )
                )
                return False

            timestamp = self.parse_timestamp(date_token, time_token)

            # creata state, to store the data
            new_state = State2(timestamp, data_file_id)

            new_state.vessel = vessel_name_token.strip('"')

            new_state.latitude = lat_degrees_token
            new_state.longitude = long_degrees_token

            try:
                valid_heading = float(heading_token)
            except ValueError:
                print(
                    "Line {}. Error in heading value {}. Couldn't convert to a number".format(
                        line_num, heading_token
                    )
                )
                return False
            if 0.0 > valid_heading >= 360.0:
                print(
                    "Line {}. Error in heading value {}. Should be be between 0 and 359.9 degrees".format(
                        line_num, heading_token
                    )
                )
                return False

            # Set heading as degree(quantity-with-unit) object
            new_state.set_heading(valid_heading * unit_registry.degree)

            try:
                valid_speed = float(speed_token)
            except ValueError:
                print(
                    "Line {}. Error in speed value {}. Couldn't convert to a number".format(
                        line_num, speed_token
                    )
                )
                return False

            # Set speed as knots(quantity-with-unit) object
            new_state.set_speed(valid_speed * unit_registry.knot)

            # and finally store it
            with data_store.session_scope():
                datafile = data_store.search_datafile_by_id(data_file_id)
                platform = data_store.add_to_platforms_from_rep(
                    new_state.get_platform(), "Fisher", "UK", "Public"
                )
                sensor = data_store.add_to_sensors_from_rep(
                    platform.name + "_GPS", platform
                )
                data_store.add_state_to_states(
                    new_state, datafile, sensor,
                )

    def degrees_for(self, degs, mins, secs, hemi: str):
        if hemi.upper() == "S" or hemi.upper() == "W":
            factor = -1
        else:
            factor = 1
        return factor * (float(degs) + float(mins) / 60 + float(secs) / 60 / 60)

    def parse_timestamp(self, date, time):
        formatStr = "%Y/%m/%d "
        # formatStr += "%H::%M::%S"

        print(datetime.strptime(date, formatStr))

        return datetime.strptime(date + " " + time, formatStr)
