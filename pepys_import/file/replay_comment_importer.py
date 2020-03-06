import os

from .importer import Importer
from pepys_import.core.validators import constants
from pepys_import.core.formats.rep_line import parse_timestamp


class ReplayCommentImporter(Importer):
    def __init__(
        self,
        name="Replay Comment Importer",
        validation_level=constants.ENHANCED_LEVEL,
        short_name="REP Comment Importer",
        separator=" ",
    ):
        super().__init__(name, validation_level, short_name)
        self.separator = separator
        self.text_label = None
        self.depth = 0.0
        self.errors = list()

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".REP"

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, first_line):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def load_this_file(self, data_store, path, file_contents, datafile):
        self.errors = list()
        basename = os.path.basename(path)
        print(f"Rep Comment parser working on '{basename}'")
        error_type = self.short_name + f" - Parsing error on '{basename}'"
        datafile.measurements[self.short_name] = list()
        for line_number, line in enumerate(file_contents, 1):
            if line.startswith(";"):
                if line.startswith(";NARRATIVE:"):
                    # ok for for it
                    tokens = line.split()

                    if len(tokens) < 5:
                        self.errors.append(
                            {
                                error_type: f"Error on line {line_number}. "
                                "Not enough tokens: {line}"
                            }
                        )
                        return False

                    # separate token strings
                    date_token = tokens[1]
                    time_token = tokens[2]
                    vessel_name_token = tokens[3]
                    message_token = tokens[4]
                    comment_type = "None"
                elif line.startswith(";NARRATIVE2:"):
                    # ok for for it
                    tokens = line.split()

                    if len(tokens) < 6:
                        self.errors.append(
                            {
                                error_type: f"Error on line {line_number}. "
                                "Not enough tokens: {line}"
                            }
                        )
                        return False

                    # separate token strings
                    date_token = tokens[1]
                    time_token = tokens[2]
                    vessel_name_token = tokens[3]
                    comment_type = tokens[4]
                    message_token = tokens[5]
                else:
                    continue

                privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
                platform = data_store.get_platform(
                    platform_name=vessel_name_token,
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                sensor_type = data_store.add_to_sensor_types("Human")
                sensor = platform.get_sensor(
                    data_store=data_store,
                    sensor_name=platform.name,
                    sensor_type=sensor_type,
                    privacy=privacy.name,
                )
                comment_type = data_store.add_to_comment_types(comment_type)
                comment = datafile.create_comment(
                    sensor=sensor,
                    timestamp=parse_timestamp(date_token, time_token),
                    comment=message_token,
                    comment_type=comment_type,
                    parser_name=self.short_name,
                )
                comment.privacy = privacy
