from .core_parser import CoreParser
from pepys_import.core.formats.state2 import State2
from pepys_import.core.formats import unit_registry


class ReplayParser(CoreParser):
    def __init__(self):
        super().__init__("Replay File Format")
        self.text_label = None
        self.depth = 0.0

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return True

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents, datafile_name):
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
                        f"Line {line_num}. Error in Date format {date_token}. Should "
                        f"be either 2 of 4 figure date, followed by month then date"
                    )
                    return False

                # Times always in Zulu/GMT
                if len(time_token) != 6 and len(time_token) != 10:
                    print(
                        f"Line {line_num}. Error in Time format {time_token}. "
                        f"Should be HHMMSS[.SSS]"
                    )
                    return False

                timestamp = self.parse_timestamp(date_token, time_token)

                # create state, to store the data
                new_state = State2(timestamp)

                new_state.vessel = vessel_name_token.strip('"')

                symbology_values = symbology_token.split("[")
                if len(symbology_values) >= 1:
                    if len(symbology_values[0]) != 2 and len(symbology_values[0]) != 5:
                        print(
                            f"Line {line_num}. Error in Symbology format "
                            f"{symbology_token}. Should be 2 or 5 chars"
                        )
                        return False
                if len(symbology_values) != 1 and len(symbology_values) != 2:
                    print(
                        f"Line {line_num}. Error in Symbology format {symbology_token}"
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
                        f"Line {line_num}. Error in heading value {heading_token}. "
                        f"Couldn't convert to a number"
                    )
                    return False
                if 0.0 > valid_heading >= 360.0:
                    print(
                        f"Line {line_num}. Error in heading value {heading_token}. "
                        f"Should be be between 0 and 359.9 degrees"
                    )
                    return False

                # Set heading as degree(quantity-with-unit) object
                new_state.set_heading(valid_heading * unit_registry.degree)

                try:
                    valid_speed = float(speed_token)
                except ValueError:
                    print(
                        f"Line {line_num}. Error in speed value {speed_token}. "
                        f"Couldn't convert to a number"
                    )
                    return False

                # Set speed as knots(quantity-with-unit) object
                new_state.set_speed(valid_speed * unit_registry.knot)

                try:
                    if not depth_token == "NaN":
                        self.depth = float(depth_token)
                except ValueError:
                    print(
                        f"Line {line_num}. Error in depth value {depth_token}. "
                        f"Couldn't convert to a number"
                    )
                    return False

                # and finally store it
                with data_store.session_scope():
                    datafile = data_store.search_datafile(datafile_name)
                    platform = data_store.get_platform(
                        platform_name=new_state.get_platform(),
                        nationality="UK",
                        platform_type="Fisher",
                        privacy="Public",
                    )

                    all_sensors = data_store.session.query(
                        data_store.db_classes.Sensor
                    ).all()
                    data_store.add_to_sensor_types("_GPS")
                    sensor = platform.get_sensor(
                        session=data_store.session,
                        all_sensors=all_sensors,
                        sensor_name=platform.name,
                        sensor_type="_GPS",
                        privacy="TEST",
                    )
                    state = datafile.create_state(sensor, new_state.timestamp)
                    state.set_location(new_state.get_location())
                    state.set_heading(
                        new_state.heading.to(unit_registry.radians).magnitude
                    )
                    state.set_speed(
                        new_state.speed.to(
                            unit_registry.meter / unit_registry.second
                        ).magnitude
                    )
                    privacy = data_store.search_privacy("TEST")
                    state.set_privacy(privacy)
                    if datafile.validate():
                        state.submit(data_store.session)

    @staticmethod
    def degrees_for(degs, mins, secs, hemi: str):
        if hemi.upper() == "S" or hemi.upper() == "W":
            factor = -1
        else:
            factor = 1
        return factor * (float(degs) + float(mins) / 60 + float(secs) / 60 / 60)
