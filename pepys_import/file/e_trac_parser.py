from .importer import Importer
from datetime import datetime
from pepys_import.core.formats import unit_registry
from pepys_import.utils.unit_utils import convert_heading, convert_speed

class ETracParser(Importer):
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

    def load_this_file(self, data_store, path, file_contents, data_file_id):
        print("E-trac parser working on ", path)
        line_num = 0
        cur_datafile_id = None
        for line in file_contents:

            line_num += 1

            # skip first line
            if line_num == 1:
                continue

            tokens = line.split(",")
            if len(tokens) == 0:
                # done
                return False
            elif len(tokens) < 17:
                print("Error on line {} not enough tokens: {}".format(line_num, line))
                return False

            # separate token strings
            date_token = tokens[2]
            time_token = tokens[3]
            lat_degrees_token = tokens[4]
            long_degrees_token = tokens[5]
            heading_token = tokens[8]
            speed_token = tokens[6]
            comp_name_token = tokens[18]
            vessel_name = self.name_for(comp_name_token)

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

            try:
                valid_speed = float(speed_token)
            except ValueError:
                print(
                    "Line {}. Error in speed value {}. Couldn't convert to a number".format(
                        line_num, speed_token
                    )
                )
                return False

            # and finally store it
            with data_store.session_scope():
                if cur_datafile_id is None:
                    datafile = data_store.search_datafile(data_file_id)
                    cur_datafile_id = datafile.datafile_id
                else:
                    datafile = data_store.get_datafile_from_id(cur_datafile_id)
                platform = data_store.get_platform(
                    platform_name=vessel_name,
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                all_sensors = data_store.session.query(
                    data_store.db_classes.Sensor
                ).all()
                data_store.add_to_sensor_types("GPS")
                sensor = platform.get_sensor(
                    session=data_store.session,
                    all_sensors=all_sensors,
                    sensor_name="E-Trac",
                    sensor_type="GPS",
                    privacy="TEST",
                )
                state = datafile.create_state(sensor, timestamp)
                privacy = data_store.search_privacy("TEST")
                state.privacy = privacy.privacy_id

                state.location = f"POINT({long_degrees_token} {lat_degrees_token})" 

                headingVal = convert_heading(heading_token, line_num)
                state.heading = headingVal.to(unit_registry.radians).magnitude

                speedVal = convert_speed(speed_token, line_num)
                state.speed = speedVal
                if datafile.validate():
                    state.submit(data_store.session)

    @staticmethod
    def name_for(token):
        # split into two
        tokens = token.split()
        return tokens[1]

    def parse_timestamp(self, date, time):
        formatStr = "%Y/%m/%d "
        formatStr += "%H:%M:%S"

        res = datetime.strptime(date.strip() + " " + time.strip(), formatStr)

        return res
