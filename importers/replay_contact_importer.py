from pepys_import.core.validators import constants
from pepys_import.core.formats.rep_line import parse_timestamp
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.core.formats.location import Location


class ReplayContactImporter(Importer):
    def __init__(
        self,
        name="Replay Contact Importer",
        validation_level=constants.ENHANCED_LEVEL,
        short_name="REP Contact Importer",
    ):
        super().__init__(name, validation_level, short_name)
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

    def _get_list_index_value(self, list, index, line_number, line, throw=True):
        if len(list) - 1 <= index:
            if throw:
                raise Exception(
                    {
                        self.error_type: f"Error on line {line_number} and index {index}. "
                        f"Not enough tokens: {line.text}"
                    }
                )
            else:
                return None
        val = list[index]
        return val if val.text != "NULL" else None

    def _load_this_file(self, data_store, path, file_object, datafile):
        for line_number, line in enumerate(file_object.lines(), 1):
            if line.text.startswith(";SENSOR:") or line.text.startswith(";SENSOR2:"):
                date_token = None
                time_token = None
                ownship_name_token = None
                symbology_token = None
                symbology_token = None
                lat_degrees_token = None
                lat_min_token = None
                lat_second_token = None
                lat_hamisphere_token = None
                long_degrees_token = None
                long_min_token = None
                long_second_token = None
                long_hamisphere_token = None
                bearing_token = None
                ambigous_bearing_token = None
                sensor_name_token = None
                label_tokens = []
                range_token = None
                frequency_token = None

                tokens = line.tokens()
                index = 0

                #  Populate token varibales.
                try:
                    index += 1
                    date_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    time_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    ownship_name_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    symbology_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    lat_degrees_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    if lat_degrees_token:
                        index += 1
                        lat_min_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        lat_second_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        lat_hamisphere_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        long_degrees_token = tokens[index]

                        index += 1
                        long_min_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        long_second_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        long_hamisphere_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                    index += 1
                    bearing_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    if line.text.startswith(";SENSOR2:"):
                        index += 1
                        ambigous_bearing_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                        index += 1
                        frequency_token = self._get_list_index_value(
                            tokens, index, line_number, line
                        )

                    index += 1
                    range_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    sensor_name_token = self._get_list_index_value(
                        tokens, index, line_number, line
                    )

                    index += 1
                    if index < len(tokens):
                        label_tokens = tokens[index:]

                except Exception as ex:
                    self.errors.append(ex.args[0])
                    continue
            else:
                continue

            # Parsing Tokens.
            timestamp = parse_timestamp(date_token.text, time_token.text)
            combine_tokens(date_token, time_token).record(
                self.name, "timestamp", timestamp, "n/a"
            )

            point = None
            if lat_degrees_token:
                latitude = Location(
                    lat_degrees_token.text,
                    lat_min_token.text,
                    lat_second_token.text,
                    lat_hamisphere_token.text,
                    errors,
                    "Latitude",
                )

                longitude = Location(
                    long_degrees_token.text,
                    long_min_token.text,
                    long_second_token.text,
                    long_hamisphere_token.text,
                    errors,
                    "Longitude",
                )

                if not latitude.parse() or not longitude.parse():
                    continue

                point = (
                    f"POINT({self.longitude.as_degrees()} {self.latitude.as_degrees()})"
                )

            bearing = None
            if bearing_token:
                try:
                    bearing = float(bearing_token.text)
                except ValueError:
                    self.errors.append(
                        {
                            self.error_type: f"Error in bearing value {bearing_token}. Couldn't convert to a number"
                        }
                    )
                    continue

            ambigous_bearing = None
            if ambigous_bearing_token:
                try:
                    ambigous_bearing = float(ambigous_bearing_token.text)
                except ValueError:
                    self.errors.append(
                        {
                            self.error_type: f"Error in ambigous bearing value {ambigous_bearing_token}. Couldn't convert to a number"
                        }
                    )
                    continue

            frequency = None
            if frequency_token:
                try:
                    frequency = float(frequency_token.text)
                except ValueError:
                    self.errors.append(
                        {
                            self.error_type: f"Error in frequency value {frequency_token}. Couldn't convert to a number"
                        }
                    )
                    continue

            range_val = None
            if range_token:
                try:
                    range_val = float(range_token.text)
                except ValueError:
                    self.errors.append(
                        {
                            self.error_type: f"Error in range value {range_token}. Couldn't convert to a number"
                        }
                    )
                    return False

            label = " ".join([t.text for t in label_tokens])
            combine_tokens(*label_tokens).record(self.name, "label", label, "n/a")

            # save data to db.
            if sensor_name_token is None:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {line_number}. "
                        f"sensor name is not defined: {line.text}"
                    }
                )
                continue

            privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
            platform = data_store.get_platform(
                platform_name=ownship_name_token.text,
                nationality="UK",
                platform_type="Fisher",
                privacy="Public",
            )
            ownship_name_token.record(
                self.name, "vessel name", ownship_name_token.text, "n/a"
            )
            sensor_type = data_store.add_to_sensor_types("Human")
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name=sensor_name_token.text,
                sensor_type=sensor_type,
                privacy=privacy.name,
            )

            contact = datafile.create_contact(
                data_store=data_store,
                platform=platform,
                sensor=sensor,
                timestamp=timestamp,
                parser_name=self.short_name,
            )
            contact.privacy = privacy
            contact.location = point
            contact.bearing = bearing
            contact.freq = frequency
            contact.name = sensor_name_token.text
            # TODO: contact.ambigous_bearing = ambigous_bearing
            # TODO: contact.symbology = symbology
            # TODO: contact.range  = range
            # TODO: contact.label = label
