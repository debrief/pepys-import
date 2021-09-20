from pepys_import.core.formats.rep_line import REPLine
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer


class ReplayImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Replay File Format Importer",
            validation_level=constants.ENHANCED_LEVEL,
            short_name="REP Importer",
            datafile_type="Replay",
        )
        self.text_label = None
        self.depth = 0.0

        # Example: Uncomment this line to turn off recording of extractions
        # for this importer
        # self.disable_recording()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line.text.startswith(";") or line.text.strip() == "":
            return

        # create state, to store the data
        rep_line = REPLine(line_number, line)
        # Store parsing errors in self.errors list
        if not rep_line.parse(self.errors, self.error_type):
            return
        # and finally store it
        vessel_name = rep_line.get_platform()
        platform = self.get_cached_platform(data_store, vessel_name, change_id=change_id)

        sensor = self.get_cached_sensor(
            data_store=data_store,
            sensor_name=None,
            sensor_type=None,
            platform_id=platform.platform_id,
            change_id=change_id,
        )

        state = datafile.create_state(
            data_store,
            platform,
            sensor,
            rep_line.timestamp,
            self.short_name,
        )

        if rep_line.depth is not None:
            state.elevation = -1 * rep_line.depth

        state.heading = rep_line.heading
        state.speed = rep_line.speed
        state.location = rep_line.get_location()

        datafile.flush_extracted_tokens()

    @staticmethod
    def degrees_for(degs, mins, secs, hemi: str):
        if hemi.upper() == "S" or hemi.upper() == "W":
            factor = -1
        else:
            factor = 1
        return factor * (float(degs) + float(mins) / 60 + float(secs) / 60 / 60)
