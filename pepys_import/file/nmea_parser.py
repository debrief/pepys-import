from .core_parser import CoreParser
from pepys_import.core.formats import unit_registry, quantity
from pepys_import.core.formats.state2 import State2
from datetime import datetime


class NMEAParser(CoreParser):
    def __init__(self):
        super().__init__("NMEA File Format")

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return "$POSL" in first_line

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents, data_file_id):
        print("NMEA parser working on " + path)

        line_num = 0
        lat_tok = None
        lat_hem_tok = None
        long_tok = None
        long_hem_tok = None
        date_tok = None
        time_tok = None
        hdg_tok = None
        spd_tok = None

        ctr = 0

        for line in file_contents:

            ctr += 1

            if ctr > 5000:
                break

            tokens = line.split(",")

            line_num += 1

            if len(tokens) > 0:

                msg_type = tokens[1]
                if msg_type == "DZA":
                    date_tok = tokens[2]
                    time_tok = tokens[3]
                elif msg_type == "VEL":
                    spd_tok = tokens[6]
                elif msg_type == "HDG":
                    hdg_tok = tokens[2]
                elif msg_type == "POS":
                    lat_tok = tokens[3]
                    lat_hem_tok = tokens[4]
                    long_tok = tokens[5]
                    long_hem_tok = tokens[6]

                # do we have all we need?
                if date_tok and spd_tok and hdg_tok and lat_tok:

                    # and finally store it
                    with data_store.session_scope():
                        datafile = data_store.search_datafile_by_id(data_file_id)
                        platform = data_store.add_to_platforms_from_rep(
                            "Toure", "Ferry", "FR", "Public"
                        )
                        sensor = data_store.add_to_sensors_from_rep(
                            platform.name + "_GPS", platform
                        )

                        date_time = self.parse_timestamp(date_tok, time_tok)
                        state = State2(date_time, sensor)

                        loc = self.parse_location(
                            lat_tok, lat_hem_tok, long_tok, long_hem_tok
                        )

                        state.set_location_obj(loc)
                        state.set_speed(
                            float(spd_tok) * unit_registry.metre / unit_registry.second
                        )
                        state.set_heading(float(hdg_tok) * unit_registry.degree)

                        data_store.add_state_to_states(
                            state, datafile, sensor,
                        )

                        date_tok = None
                        spd_tok = None
                        hdg_tok = None
                        lat_tok = None

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

    def parse_location(self, lat, lat_hem, lon, long_hem):
        latDegs = float(lat[0:2])
        latMins = float(lat[2:4])
        latSecs = float(lat[4:])
        latDegs = latDegs + latMins / 60 + latSecs / 60 / 60

        lonDegs = float(lon[0:3])
        lonMins = float(lon[3:5])
        lonSecs = float(lon[5:])
        lonDegs = lonDegs + lonMins / 60 + lonSecs / 60 / 60

        if lat_hem == "S":
            latDegs = -1 * latDegs

        if lat_hem == "W":
            lonDegs = -1 * lonDegs

        return (latDegs, lonDegs)
