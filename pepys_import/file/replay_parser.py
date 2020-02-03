from .core_parser import CoreParser
from pepys_import.core.formats.state2 import State2
from datetime import datetime
from pepys_import.core.formats.location import Location
from pepys_import.core.formats import unit_registry, quantity


class ReplayParser(CoreParser):
    def __init__(self):
        super().__init__("Replay File Format")

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return True

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents, data_file_id):
        print("Rep parser working on " + path)
        line_num = 0
        for line in file_contents:

            line_num += 1

            if line.startswith(";"):
                pass
            else:
                tokens = line.split()

                if len(tokens) < 15:
                    print(
                        "Error on line {} not enough tokens: {}".format(line_num, line)
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
                    # TODO: join back into single string, or extract full substring
                    self.text_label = tokens[15:]

                if len(date_token) != 6 and len(date_token) != 8:
                    print(
                        "Line {}. Error in Date format {}. Should be either 2 of 4 figure date, followed by month then date".format(
                            line_num, date_token
                        )
                    )
                    return False

                # Times always in Zulu/GMT
                if len(time_token) != 6 and len(time_token) != 10:
                    print(
                        "Line {}. Error in Time format {}. Should be HHMMSS[.SSS]".format(
                            line_num, time_token
                        )
                    )
                    return False

                timestamp = self.parse_timestamp(date_token, time_token)

                # creata state, to store the data
                new_state = State2(timestamp, data_file_id)

                new_state.vessel = vessel_name_token.strip('"')

                symbology_values = symbology_token.split("[")
                if len(symbology_values) >= 1:
                    if len(symbology_values[0]) != 2 and len(symbology_values[0]) != 5:
                        print(
                            "Line {}. Error in Symbology format {}. Should be 2 or 5 chars".format(
                                line_num, symbology_token
                            )
                        )
                        return False
                if len(symbology_values) != 1 and len(symbology_values) != 2:
                    print(
                        "Line {}. Error in Symbology format {}".format(
                            line_num, symbology_token
                        )
                    )
                    return False

                new_state.symbology = symbology_token

                new_state.latitude = self.degrees_for(
                    lat_degrees_token, lat_mins_token, lat_secs_token, lat_hemi_token
                )

                new_state.longitude = self.degrees_for(
                    long_degrees_token,
                    long_mins_token,
                    long_secs_token,
                    long_hemi_token,
                )

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

                try:
                    if depth_token == "NaN":
                        self.depth = 0.0
                    else:
                        self.depth = float(depth_token)
                except ValueError:
                    print(
                        "Line {}. Error in depth value {}. Couldn't convert to a number".format(
                            line_num, depth_token
                        )
                    )
                    return False

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
        if len(date) == 6:
            formatStr = "%y%m%d"
        else:
            formatStr = "%Y%m%d"

        if len(time) == 6:
            formatStr += "%H%M%S"
        else:
            formatStr += "%H%M%S.%f"

        return datetime.strptime(date + time, formatStr)
