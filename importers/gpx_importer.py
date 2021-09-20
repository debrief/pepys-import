from dateutil.parser import parse as date_parse
from dateutil.tz import tzoffset
from tqdm import tqdm

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.xml_parser import parse
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed


class GPXImporter(Importer):
    def __init__(self):
        super().__init__(
            name="GPX Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="GPX Importer",
            datafile_type="GPX",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".GPX"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        # Can't tell from first line only whether file is a valid GPX file
        return True

    def can_load_this_file(self, file_contents):
        # TODO: Check here to see if we can parse file with XML parser without exceptions raised
        # But note we can't do this from the file_contents variable as lxml
        # won't parse a string with an encoding attribute - it requires bytes instead
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # Parse XML file from the full path of the file
        # Note: we can't use the file_object variable passed in, as lxml refuses
        # to parse a string that has an encoding attribute in the XML - it requires bytes instead
        try:
            doc = parse(path, highlighted_file=file_object)
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Invalid GPX file at {path}\nError from parsing was "{str(e)}"'}
            )
            return

        # Iterate through <trk> elements - these should correspond to
        # a specific platform, with the platform name in the <name> element
        for track_element in tqdm(doc.findall(".//{*}trk")):
            track_name_element = track_element.find("{*}name")
            track_name = track_name_element.text
            track_name_element.record(self.name, "name", track_name)

            # Get the platform and sensor details, as these will be the same for all
            # points in this track
            platform = self.get_cached_platform(
                data_store, platform_name=track_name, change_id=change_id
            )
            sensor_type = data_store.add_to_sensor_types(
                "Location-Satellite", change_id=change_id
            ).name
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name="GPS",
                sensor_type=sensor_type,
                change_id=change_id,
            )

            # Get all <trkpt> children of this track
            # (no matter which <trkseg> they are in - as all <trkseg> elements below this
            # belong to this track)
            for tpt in track_element.findall(".//{*}trkpt"):
                # Extract information (location, speed etc) from <trkpt> element
                timestamp_el, timestamp_str = self.get_child_and_text_if_exists(tpt, "{*}time")

                if timestamp_str is None:
                    self.errors.append(
                        {
                            self.error_type: f"Line {tpt.sourceline} "
                            "Error: <trkpt> element must have child <time> element"
                        }
                    )
                    continue

                timestamp = self.parse_timestamp(timestamp_str)
                if not timestamp:
                    self.errors.append(
                        {
                            self.error_type: f"Line {timestamp_el.sourceline}. "
                            f"Error: Invalid timestamp {timestamp_str}"
                        }
                    )
                    continue

                timestamp_el.record(self.name, "timestamp", timestamp)

                speed_el, speed_str = self.get_child_and_text_if_exists(tpt, "{*}speed")
                course_el, course_str = self.get_child_and_text_if_exists(tpt, "{*}course")
                elevation_el, elevation_str = self.get_child_and_text_if_exists(tpt, "{*}ele")

                state = datafile.create_state(
                    data_store, platform, sensor, timestamp, self.short_name
                )

                latitude_str = tpt.attrib["lat"]
                longitude_str = tpt.attrib["lon"]

                location = Location(errors=self.errors, error_type=self.error_type)
                lat_valid = location.set_latitude_decimal_degrees(latitude_str)
                lon_valid = location.set_longitude_decimal_degrees(longitude_str)

                tpt.record(self.name, "location", location, xml_part="opening")

                if lat_valid and lon_valid:
                    state.location = location

                # Add course
                if course_str is not None:
                    # Mark line number as Unknown here
                    course_valid, course = convert_absolute_angle(
                        course_str, "Unknown", self.errors, self.error_type
                    )
                    course_el.record(self.name, "course", course)
                    if course_valid:
                        state.course = course

                # Add speed (specified in metres per second in the file)
                if speed_str is not None:
                    speed_valid, speed = convert_speed(
                        speed_str,
                        (unit_registry.metre / unit_registry.second),
                        None,
                        self.errors,
                        self.error_type,
                    )
                    speed_el.record(self.name, "speed", speed)
                    if speed_valid:
                        state.speed = speed

                if elevation_str is not None:
                    elevation_valid, elevation = convert_distance(
                        elevation_str, unit_registry.metre, None, self.errors, self.error_type
                    )
                    elevation_el.record(self.name, "elevation", elevation)
                    if elevation_valid:
                        state.elevation = elevation

                datafile.flush_extracted_tokens()

    def get_child_and_text_if_exists(self, element, search_string):
        child = element.find(search_string)
        if child is not None:
            return child, child.text
        return None, None

    def parse_timestamp(self, s):
        try:
            dt = date_parse(s)
        except Exception:
            return False

        # Create a UTC time zone object
        utc = tzoffset("UTC", 0)

        # Convert to UTC
        dt_in_utc = dt.astimezone(utc)

        # Convert to a 'naive' datetime - ie. without a timezone
        dt_naive = dt_in_utc.replace(tzinfo=None)

        return dt_naive
