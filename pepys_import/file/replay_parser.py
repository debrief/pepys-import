from .core_parser import CoreParser
from pepys_import.core.formats.rep_line import REPLine
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
        for line_number, line in enumerate(file_contents):
            if line.startswith(";"):
                continue
            else:
                # create state, to store the data
                rep_line = REPLine(line_number + 1, line)
                if not rep_line.parse():
                    continue

                # and finally store it
                with data_store.session_scope():
                    datafile = data_store.search_datafile(datafile_name)
                    platform = data_store.get_platform(
                        platform_name=rep_line.get_platform(),
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
                    state = datafile.create_state(sensor, rep_line.timestamp)
                    state.set_location(rep_line.get_location())
                    state.set_heading(
                        rep_line.heading.to(unit_registry.radians).magnitude
                    )
                    state.set_speed(rep_line.speed)
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
