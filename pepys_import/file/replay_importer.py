from .importer import Importer
from pepys_import.core.formats.rep_line import REPLine
from pepys_import.core.formats import unit_registry
from pepys_import.core.validators import constants


class ReplayImporter(Importer):
    name = "Replay File Format Importer"
    validation_level = constants.ENHANCED_LEVEL
    short_name = "REP Importer"

    def __init__(self, separator=" "):
        super().__init__()
        self.separator = separator
        self.text_label = None
        self.depth = 0.0
        self.errors = list()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_contents, datafile):
        print("Rep parser working on " + path)
        error_message = self.short_name + f" - Parsing error on {path}"
        for line_number, line in enumerate(file_contents, 1):
            if line.startswith(";"):
                continue
            else:
                # create state, to store the data
                rep_line = REPLine(line_number, line, self.separator)
                # Store parsing errors in self._error list
                if not rep_line.parse(self.errors, error_message):
                    continue

                # and finally store it
                platform = data_store.get_platform(
                    platform_name=rep_line.get_platform(),
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )

                sensor_type = data_store.add_to_sensor_types("_GPS")
                privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
                sensor = platform.get_sensor(
                    data_store=data_store,
                    sensor_name=platform.name,
                    sensor_type=sensor_type,
                    privacy=privacy.name,
                )
                state = datafile.create_state(sensor, rep_line.timestamp)
                state.location = rep_line.get_location()
                state.elevation = -1 * rep_line.depth
                state.heading = rep_line.heading.to(unit_registry.radians).magnitude

                state.speed = rep_line.speed
                state.privacy = privacy.privacy_id

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
