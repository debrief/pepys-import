from .importer import Importer
from pepys_import.core.formats.rep_line import REPLine
from pepys_import.core.formats import unit_registry


class ReplayImporter(Importer):
    name = "Replay File Format Importer"

    def __init__(self, separator=" "):
        super().__init__()
        self.separator = separator
        self.text_label = None
        self.depth = 0.0

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_contents, datafile_name):
        print("Rep parser working on " + path)
        for line_number, line in enumerate(file_contents):
            if line.startswith(";"):
                continue
            else:
                # create state, to store the data
                rep_line = REPLine(line_number + 1, line, self.separator)
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
                    state.location = rep_line.get_location()
                    state.heading = rep_line.heading.to(unit_registry.radians).magnitude

                    state.speed = rep_line.speed
                    privacy = data_store.search_privacy("TEST")
                    state.privacy = privacy.privacy_id
                    if datafile.validate():
                        state.submit(data_store.session)

    # def requires_user_review(self) -> bool:
    #     """
    #     Whether this importer requires user review of the loaded intermediate data
    #     before pushing to the database.  The review may be by viewing an HTML import
    #     summary, or examining some statistical/graphical overview.
    #
    #     :return: True or False
    #     :rtype: bool
    #     """
    #     pass
    #
    @staticmethod
    def degrees_for(degs, mins, secs, hemi: str):
        if hemi.upper() == "S" or hemi.upper() == "W":
            factor = -1
        else:
            factor = 1
        return factor * (float(degs) + float(mins) / 60 + float(secs) / 60 / 60)
