from dateutil.parser import parse
from lxml import etree

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_speed


class GPXImporter(Importer):
    def __init__(
        self,
        name="GPX Format Importer",
        validation_level=constants.BASIC_LEVEL,
        short_name="GPX Importer",
        separator=" ",
    ):
        super().__init__(name, validation_level, short_name)
        self.errors = list()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".GPX"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        # Can't tell from first line only whether file is a valid GPX file
        return True

    def can_load_this_file(self, file_contents):
        # TODO: Check here to see if we can parse file with XML parser without exceptions raised
        # But note we can't do this from the file_contents variable as lxml
        # won't parse a string with an encoding attribute - it requires bytes instead
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # Parse XML file from the full path of the file
        # Note: we can't use the file_contents variable passed in, as lxml refuses
        # to parse a string that has an encoding attribute in the XML - it requires bytes instead
        try:
            doc = etree.parse(path)
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Invalid GPX file at {path}\nError from parsing was "{str(e)}"'}
            )
            return

        # Iterate through <trk> elements - these should correspond to
        # a specific platform, with the platform name in the <name> element
        for track_element in doc.findall("//{*}trk"):
            track_name = track_element.find("{*}name").text

            # Get the platform and sensor details, as these will be the same for all
            # points in this track
            platform = data_store.get_platform(
                platform_name=track_name,
                nationality="UK",
                platform_type="Fisher",
                privacy="Public",
                change_id=change_id,
            )
            sensor_type = data_store.add_to_sensor_types("GPS", change_id=change_id)
            privacy = data_store.missing_data_resolver.resolve_privacy(data_store, change_id)
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name="GPX",
                sensor_type=sensor_type,
                privacy=privacy.name,
                change_id=change_id,
            )

            # Get all <trkpt> children of this track
            # (no matter which <trkseg> they are in - as all <trkseg> elements below this
            # belong to this track)
            for tpt in track_element.findall(".//{*}trkpt"):
                # Extract information (location, speed etc) from <trkpt> element
                latitude_str = tpt.attrib["lat"]
                longitude_str = tpt.attrib["lon"]

                timestamp_str = self.get_child_text_if_exists(tpt, "{*}time")

                if timestamp_str is None:
                    self.errors.append(
                        {
                            self.error_type: f"Line {tpt.sourceline}. "
                            f"Error: <trkpt> element must have child <time> element"
                        }
                    )
                    continue

                speed_str = self.get_child_text_if_exists(tpt, "{*}speed")
                course_str = self.get_child_text_if_exists(tpt, "{*}course")
                elevation_str = self.get_child_text_if_exists(tpt, "{*}ele")

                # Parse timestamp and create state
                timestamp = parse(timestamp_str)
                state = datafile.create_state(
                    data_store, platform, sensor, timestamp, self.short_name
                )

                # Add location (no need to convert as it requires a string)
                if track_name in self.prev_location:
                    state.prev_location = self.prev_location[track_name]

                location = Location(errors=self.errors, error_type=self.error_type)
                location.set_latitude_decimal_degrees(latitude_str)
                location.set_longitude_decimal_degrees(longitude_str)

                state.location = location
                self.prev_location[track_name] = state.location

                # Add course
                if course_str is not None:
                    course = convert_absolute_angle(
                        course_str, tpt.sourceline, self.errors, self.error_type
                    )
                    state.course = course

                # Add speed (specified in metres per second in the file)
                if speed_str is not None:
                    speed = convert_speed(
                        speed_str,
                        (unit_registry.metre / unit_registry.second),
                        None,
                        self.errors,
                        self.error_type,
                    )
                    if speed:
                        state.speed = speed

                if elevation_str is not None:
                    try:
                        elevation = float(elevation_str)
                    except ValueError:
                        self.errors.append(
                            {
                                self.error_type: f"Line {tpt.sourceline}. Error in elevation value {elevation_str}. "
                                f"Couldn't convert to number"
                            }
                        )
                    state.elevation = elevation * unit_registry.metre

                state.privacy = privacy.privacy_id

    def get_child_text_if_exists(self, element, search_string):
        child = element.find(search_string)
        if child is not None:
            return child.text
        else:
            return None
