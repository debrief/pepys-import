from datetime import datetime

from tqdm import tqdm

from pepys_import.core.validators import constants
from pepys_import.file.highlighter.xml_parser import parse
from pepys_import.file.importer import Importer


class OrcaImporter(Importer):
    """Importer for data exported from the Oceanographic Reconnaissance and Combat
    Architecture (ORCA) system.
    """

    def __init__(self):
        super().__init__(
            name="ORCA Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="ORCA Importer",
            default_privacy="Private",
            datafile_type="ORCA",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".XML"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        # TODO - confirm this is actually the header
        return header.startswith('<ns2:datafile xmlns:ns2="mw">')

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # TODO:
        # - Read in the file
        # - Parse the platform
        # - Parse the tracks

        # Re-read the data file with the Pepys xml parser
        try:
            doc = parse(path, highlighted_file=file_object)
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Invalid ORCA file at {path}\nError from parsing was "{str(e)}"'}
            )
            return
        # Now start parsing
        for mission in tqdm(doc.findall(".//{*}mission")):
            platform_name_element = mission.find("{*}unitname")
            platform_name = platform_name_element.text
            platform = self.get_cached_platform(
                data_store, platform_name=platform_name, change_id=change_id
            )

            sensor_type = data_store.add_to_sensor_types("Location-ORCA", change_id=change_id).name
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name="ORCA",  # TODO - should this also be GPS?
                sensor_type=sensor_type,
                change_id=change_id,
            )

            # TODO - get timestamp from the actual data
            # Note that example only has a "creation time" for a track

            timestamp = datetime(2021, 10, 15, 1, 2, 3)
            state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)

            print(state)

            datafile.flush_extracted_tokens()
