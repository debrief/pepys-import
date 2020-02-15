from .importer import Importer
from datetime import datetime

from pepys_import.utils.unit_utils import convert_heading, convert_speed


class NMEAImporter(Importer):
    name = "NMEA File Format Importer"

    def __init__(self):
        super().__init__()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return "$POSL" in first_line

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_contents, datafile_name):
        print("NMEA parser working on " + path)

        lat_token = None
        lat_hem_token = None
        long_token = None
        long_hem_token = None
        date_token = None
        time_token = None
        hdg_token = None
        spd_token = None

        for line_number, line in enumerate(file_contents):
            if line_number > 5000:
                break
            tokens = line.split(",")
            if len(tokens) > 0:

                msg_type = tokens[1]
                if msg_type == "DZA":
                    date_token = tokens[2]
                    time_token = tokens[3]
                elif msg_type == "VEL":
                    spd_token = tokens[6]
                elif msg_type == "HDG":
                    hdg_token = tokens[2]
                elif msg_type == "POS":
                    lat_token = tokens[3]
                    lat_hem_token = tokens[4]
                    long_token = tokens[5]
                    long_hem_token = tokens[6]

                # do we have all we need?
                if date_token and time_token and spd_token and hdg_token and lat_token:

                    # and finally store it
                    with data_store.session_scope():
                        datafile = data_store.search_datafile(datafile_name)
                        platform = data_store.get_platform(
                            "Toure", "Ferry", "FR", "Public"
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
                        timestamp = self.parse_timestamp(date_token, time_token)

                        state = datafile.create_state(sensor, timestamp)
                        location = self.parse_location(
                            lat_token, lat_hem_token, long_token, long_hem_token
                        )
                        state.set_location(location)

                        heading = convert_heading(hdg_token, line_number)
                        if heading:
                            state.set_heading(heading)

                        speed = convert_speed(spd_token, line_number)
                        if speed:
                            state.set_speed(speed)

                        privacy = data_store.search_privacy("TEST")
                        state.set_privacy(privacy)
                        if datafile.validate():
                            state.submit(data_store.session)

                        date_token = None
                        time_token = None
                        spd_token = None
                        hdg_token = None
                        lat_token = None

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
