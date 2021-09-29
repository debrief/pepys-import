from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.formats.rep_line import parse_timestamp
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import (
    convert_absolute_angle,
    convert_distance,
    convert_frequency,
)


class ReplayContactImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Replay Contact Importer",
            validation_level=constants.ENHANCED_LEVEL,
            short_name="REP Contact Importer",
            datafile_type="Replay",
        )
        self.text_label = None
        self.depth = 0.0

    def can_load_this_type(self, suffix):
        return suffix.upper() in [".REP", ".DSF"]

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        if line.text.strip() == "":
            return
        if line.text.startswith(";"):
            # we'll be using this value to determine if we have location
            lat_degrees_token = None
            ambig_bearing_token = None
            freq_token = None
            if line.text.startswith(";SENSOR:"):
                # ok for for it
                tokens = line.tokens()

                if len(tokens) < 5:
                    self.errors.append(
                        {
                            self.error_type: f"Error on line {line_number}. "
                            f"Not enough tokens: {line.text}"
                        }
                    )
                    return

                # separate token strings
                date_token = tokens[1]
                time_token = tokens[2]
                vessel_name_token = tokens[3]
                # symbology = tokens[4]

                # the next one may be degs, or it may be NULL
                next_token = tokens[5]
                if next_token.text.upper() == "NULL":
                    location = None
                    token_ctr = 5
                else:
                    token_ctr = 12
                    lat_degrees_token = tokens[5]
                    lat_mins_token = tokens[6]
                    lat_secs_token = tokens[7]
                    lat_hemi_token = tokens[8]
                    long_degrees_token = tokens[9]
                    long_mins_token = tokens[10]
                    long_secs_token = tokens[11]
                    long_hemi_token = tokens[12]

                token_ctr += 1
                bearing_token = tokens[token_ctr]

                token_ctr += 1
                range_token = tokens[token_ctr]

                token_ctr += 1
                sensor_name = tokens[token_ctr]

                sensor_name.record(self.name, "sensor", sensor_name.text)

                token_ctr += 1
                # label = tokens[token_ctr:]

            elif line.text.startswith(";SENSOR2:"):
                # ok for for it
                tokens = line.tokens()

                if len(tokens) < 5:
                    self.errors.append(
                        {
                            self.error_type: f"Error on line {line_number}. "
                            f"Not enough tokens: {line.text}"
                        }
                    )
                    return

                # separate token strings
                date_token = tokens[1]
                time_token = tokens[2]
                vessel_name_token = tokens[3]
                # symbology = tokens[4]

                # the next one may be degs, or it may be NULL
                next_token = tokens[5]
                if next_token.text.upper() == "NULL":
                    location = None
                    token_ctr = 5
                else:
                    token_ctr = 12
                    lat_degrees_token = tokens[5]
                    lat_mins_token = tokens[6]
                    lat_secs_token = tokens[7]
                    lat_hemi_token = tokens[8]
                    long_degrees_token = tokens[9]
                    long_mins_token = tokens[10]
                    long_secs_token = tokens[11]
                    long_hemi_token = tokens[12]

                token_ctr += 1
                bearing_token = tokens[token_ctr]

                token_ctr += 1
                ambig_bearing_token = tokens[token_ctr]

                token_ctr += 1
                freq_token = tokens[token_ctr]

                token_ctr += 1
                range_token = tokens[token_ctr]

                token_ctr += 1
                sensor_name = tokens[token_ctr]

                sensor_name.record(self.name, "sensor", sensor_name.text)

                token_ctr += 1
                # label = tokens[token_ctr:]

            else:
                return

            # do we have location?
            if lat_degrees_token is None:
                location = None
            else:
                loc = Location(self.errors, self.error_type)

                if not loc.set_latitude_dms(
                    lat_degrees_token.text,
                    lat_mins_token.text,
                    lat_secs_token.text,
                    lat_hemi_token.text,
                ):
                    self.errors.append(
                        {self.error_type: f"Line {line_number}. Error in latitude parsing"}
                    )
                    return

                combine_tokens(
                    lat_degrees_token,
                    lat_mins_token,
                    lat_secs_token,
                    lat_hemi_token,
                ).record(self.name, "latitude", loc, "DMS")

                if not loc.set_longitude_dms(
                    long_degrees_token.text,
                    long_mins_token.text,
                    long_secs_token.text,
                    long_hemi_token.text,
                ):
                    self.errors.append(
                        {self.error_type: f"Line {line_number}. Error in longitude parsing"}
                    )
                    return

                combine_tokens(
                    long_degrees_token,
                    long_mins_token,
                    long_secs_token,
                    long_hemi_token,
                ).record(self.name, "longitude", loc, "DMS")

                location = loc

            platform = self.get_cached_platform(
                data_store, platform_name=vessel_name_token.text, change_id=change_id
            )
            vessel_name_token.record(self.name, "vessel name", vessel_name_token.text)
            sensor = platform.get_sensor(
                data_store=data_store,
                sensor_name=sensor_name.text,
                change_id=change_id,
            )

            timestamp = parse_timestamp(date_token.text, time_token.text)
            combine_tokens(date_token, time_token).record(self.name, "timestamp", timestamp)

            contact = datafile.create_contact(
                data_store=data_store,
                platform=platform,
                sensor=sensor,
                timestamp=timestamp,
                parser_name=self.short_name,
            )
            contact.location = location

            if bearing_token.text.upper() == "NULL":
                bearing = None
            else:
                bearing_valid, bearing = convert_absolute_angle(
                    bearing_token.text, line, self.errors, self.error_type
                )
                if bearing_valid:
                    bearing_token.record(self.name, "bearing", bearing, "degs")
                    contact.bearing = bearing

            if range_token.text.upper() != "NULL":
                range_valid, range_val = convert_distance(
                    range_token.text,
                    unit_registry.yard,
                    line,
                    self.errors,
                    self.error_type,
                )
                if range_valid:
                    range_token.record(self.name, "range", range_val)
                    contact.range = range_val

            if freq_token is not None:
                if freq_token.text.upper() != "NULL":
                    freq_valid, freq_val = convert_frequency(
                        freq_token.text,
                        unit_registry.hertz,
                        line,
                        self.errors,
                        self.error_type,
                    )
                    if freq_valid:
                        freq_token.record(self.name, "frequency", freq_val)
                        contact.freq = freq_val

            if ambig_bearing_token is not None:
                if ambig_bearing_token.text.upper() == "NULL":
                    ambig_bearing = 0
                else:
                    ambig_bearing_valid, ambig_bearing = convert_absolute_angle(
                        ambig_bearing_token.text, line, self.errors, self.error_type
                    )
                    if ambig_bearing_valid:
                        ambig_bearing_token.record(self.name, "ambig bearing", ambig_bearing)
                        contact.ambig_bearing = ambig_bearing

            datafile.flush_extracted_tokens()
