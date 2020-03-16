import os

from pepys_import.core.formats.rep_line import REPLine
from pepys_import.core.formats import unit_registry
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class ReplayImporter(Importer):
    def __init__(
        self,
        name="Replay File Format Importer",
        validation_level=constants.ENHANCED_LEVEL,
        short_name="REP Importer",
        separator=" ",
    ):
        super().__init__(name, validation_level, short_name)
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

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        for line_number, line in enumerate(file_object.lines(), 1):
            if line.text.startswith(";"):
                continue
            else:
                # create state, to store the data
                rep_line = REPLine(line_number, line, self.separator)
                # Store parsing errors in self.errors list
                if not rep_line.parse(self.errors, self.error_type):
                    continue
                # and finally store it
                vessel_name = rep_line.get_platform()
                platform = data_store.get_platform(
                    platform_name=vessel_name,
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                    change_id=change_id,
                )

                sensor_type = data_store.add_to_sensor_types(
                    "_GPS", change_id=change_id
                )
                privacy = data_store.missing_data_resolver.resolve_privacy(
                    data_store, change_id
                )
                sensor = platform.get_sensor(
                    data_store=data_store,
                    sensor_name=platform.name,
                    sensor_type=sensor_type,
                    privacy=privacy.name,
                    change_id=change_id,
                )
                state = datafile.create_state(
                    data_store, platform, sensor, rep_line.timestamp, self.short_name
                )
                state.elevation = -1 * rep_line.depth
                state.heading = rep_line.heading.to(unit_registry.radians).magnitude
                state.speed = rep_line.speed
                state.privacy = privacy.privacy_id

                if vessel_name in self.prev_location:
                    state.prev_location = self.prev_location[vessel_name]

                state.location = rep_line.get_location()
                self.prev_location[vessel_name] = state.location

    @staticmethod
    def degrees_for(degs, mins, secs, hemi: str):
        if hemi.upper() == "S" or hemi.upper() == "W":
            factor = -1
        else:
            factor = 1
        return factor * (float(degs) + float(mins) / 60 + float(secs) / 60 / 60)
