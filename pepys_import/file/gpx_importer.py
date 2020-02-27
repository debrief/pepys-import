from lxml import etree
from datetime import datetime
from dateutil.parser import parse

from .importer import Importer
from pepys_import.core.formats import unit_registry
from pepys_import.utils.unit_utils import convert_heading, convert_speed


class GPXImporter(Importer):
    name = "GPX Format Importer"

    def __init__(self, separator=" "):
        super().__init__()

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

    def load_this_file(self, data_store, path, file_contents, data_file_id):
        print("GPX parser working on ", path.path)

        # Parse XML file from the full path of the file
        # Note: we can't use the file_contents variable passed in, as lxml refuses
        # to parse a string that has an encoding attribute in the XML - it requires bytes instead
        try:
            doc = etree.parse(path.path)
        except Exception as e:
            print(f'Invalid GPX file at {path.path}\nError from parsing was "{str(e)}"')
            return

        cur_datafile_id = None

        # Iterate through <trk> elements - these should correspond to
        # a specific platform, with the platform name in the <name> element
        for track_element in doc.findall("//{*}trk"):
            track_name = track_element.find("{*}name").text
            print(f"New track: {track_name}")

            # Get all <trkpt> children of this track
            # (no matter which <trkseg> they are in - as all <trkseg> elements below this
            # belong to this track)
            for tpt in track_element.findall(".//{*}trkpt"):
                # Extract information (location, speed etc) from <trkpt> element
                latitude_str = tpt.attrib["lat"]
                longitude_str = tpt.attrib["lon"]

                timestamp_str = self.get_child_text_if_exists(tpt, "{*}time")

                if timestamp_str is None:
                    print(
                        f"Line {tpt.sourceline}. Error: <trkpt> element must have child <time> element"
                    )
                    continue

                speed_str = self.get_child_text_if_exists(tpt, "{*}speed")
                course_str = self.get_child_text_if_exists(tpt, "{*}course")
                elevation_str = self.get_child_text_if_exists(tpt, "{*}ele")

                print(
                    latitude_str,
                    longitude_str,
                    timestamp_str,
                    speed_str,
                    course_str,
                    elevation_str,
                )

                # Get platform and sensor
                with data_store.session_scope():
                    if cur_datafile_id is None:
                        datafile = data_store.search_datafile(data_file_id)
                        cur_datafile_id = datafile.datafile_id
                    else:
                        datafile = data_store.get_datafile_from_id(cur_datafile_id)
                    platform = data_store.get_platform(
                        platform_name=track_name,
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
                        sensor_name="GPX",
                        sensor_type="GPS",
                        privacy="TEST",
                    )

                    # Parse timestamp and create state
                    timestamp = parse(timestamp_str)
                    state = datafile.create_state(sensor, timestamp)

                    # Add location (no need to convert as it requires a string)
                    state.location = f"POINT({longitude_str} {latitude_str})"

                    # Add course
                    if course_str is not None:
                        course = convert_heading(course_str, tpt.sourceline)
                        state.course = course.to(unit_registry.radians).magnitude

                    if speed_str is not None:
                        try:
                            speed = float(speed_str)
                        except ValueError:
                            print(
                                f"Line {tpt.sourceline}. Error in speed value {speed_str}. Couldn't convert to number"
                            )
                        state.speed = speed

                    # if elevation_str is not None:
                    #     try:
                    #         elevation = float(elevation_str)
                    #     except ValueError:
                    #         print(f"Line {tpt.sourceline}. Error in elevation value {elevation_str}. Couldn't convert to number")
                    #     state.elevation = elevation

                    privacy = data_store.search_privacy("TEST")
                    state.privacy = privacy.privacy_id

                    if datafile.validate():
                        state.submit(data_store.session)

    def get_child_text_if_exists(self, element, search_string):
        child = element.find(search_string)
        if child is not None:
            return child.text
        else:
            return None
