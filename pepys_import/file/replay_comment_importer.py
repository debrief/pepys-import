from .importer import Importer
from pepys_import.core.validators import constants
from pepys_import.core.formats.rep_line import parse_timestamp
from pepys_import.file.highlighter.support.combine import combine_tokens


class ReplayCommentImporter(Importer):
    def __init__(
        self,
        name="Replay Comment Importer",
        validation_level=constants.ENHANCED_LEVEL,
        short_name="REP Comment Importer",
    ):
        super().__init__(name, validation_level, short_name)
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

    def load_this_file(self, data_store, path, file_object, datafile):
        for line_number, line in enumerate(file_object.lines(), 1):
            if line.text.startswith(";"):
                if line.text.startswith(";NARRATIVE:"):
                    # ok for for it
                    tokens = line.tokens()

                    if len(tokens) < 5:
                        self.errors.append(
                            {
                                self.error_type: f"Error on line {line_number}. "
                                f"Not enough tokens: {line.text}"
                            }
                        )
                        continue

                    # separate token strings
                    date_token = tokens[1]
                    time_token = tokens[2]
                    vessel_name_token = tokens[3]
                    message_token = tokens[4]
                    comment_type = "None"
                elif line.text.startswith(";NARRATIVE2:"):
                    # ok for for it
                    tokens = line.tokens()

                    if len(tokens) < 6:
                        self.errors.append(
                            {
                                self.error_type: f"Error on line {line_number}. "
                                f"Not enough tokens: {line.text}"
                            }
                        )
                        continue

                    # separate token strings
                    date_token = tokens[1]
                    time_token = tokens[2]
                    vessel_name_token = tokens[3]
                    comment_type_token = tokens[4]
                    comment_type = comment_type_token.text
                    comment_type_token.record(
                        self.name, "comment type", comment_type, "n/a"
                    )
                    message_token = tokens[5]
                else:
                    continue

                privacy = data_store.missing_data_resolver.resolve_privacy(data_store)
                platform = data_store.get_platform(
                    platform_name=vessel_name_token.text,
                    nationality="UK",
                    platform_type="Fisher",
                    privacy="Public",
                )
                vessel_name_token.record(
                    self.name, "vessel name", vessel_name_token.text, "n/a"
                )
                sensor_type = data_store.add_to_sensor_types("Human")
                sensor = platform.get_sensor(
                    data_store=data_store,
                    sensor_name=platform.name,
                    sensor_type=sensor_type,
                    privacy=privacy.name,
                )
                comment_type = data_store.add_to_comment_types(comment_type)

                timestamp = parse_timestamp(date_token.text, time_token.text)
                combine_tokens(date_token, time_token).record(
                    self.name, "timestamp", timestamp, "n/a"
                )

                message = message_token.text
                message_token.record(self.name, "message", message, "n/a")

                comment = datafile.create_comment(
                    platform_id=platform.platform_id,
                    timestamp=timestamp,
                    comment=message,
                    comment_type=comment_type,
                    parser_name=self.short_name,
                )
                comment.privacy = privacy
