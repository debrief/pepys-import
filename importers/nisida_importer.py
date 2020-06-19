from datetime import datetime

from tqdm import tqdm

from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.validators import constants
from pepys_import.file.highlighter.support.combine import combine_tokens
from pepys_import.file.importer import Importer
from pepys_import.utils.unit_utils import convert_absolute_angle, convert_distance, convert_speed


class NisidaImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Nisida Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Nisida Importer",
        )
        self.current_line_no = None
        self.last_entry = None
        self.month = None
        self.year = None
        self.platform = None

    def can_load_this_type(self, suffix):
        return True

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return "UNIT/" in header

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        self.current_line_no = line_number

        if line.text.startswith("UNIT/"):
            # Handle UNIT line giving month, year and platform
            self.month = 5
            self.year = 2015
            pass
        elif line.text.startswith("//"):
            # This is a continuation of the previous line, so add whatever else is in this line
            # to the comments field of the previous entry
            print(f"Processing continuation with text {line.text}")

            if self.last_entry is None:
                self.errors.append(
                    {
                        self.error_type: f"Error on line {self.current_line_no}. "
                        f"Line continuation not immediately after valid line: {line.text}"
                    }
                )
                return

            if line.text.endswith("/"):
                text_to_add = line.text[2:-1]
            else:
                text_to_add = line.text[2:]
            self.last_entry.content = self.last_entry.content + text_to_add
        elif len(line.text) > 7 and line.text[7] == "/" and line.text[0:5].isdigit():
            # Line starts with something like "311206Z/" (a timestamp and a slash)
            # Checking like this is faster than using regular expressions on each line

            # Reset last_entry, so that if continuation characters aren't directly
            # after an entry we processed, then we will raise an error rather than
            # add to the incorrect entry
            self.last_entry = None

            # Split line by slash
            self.tokens = line.tokens("[^/]+")
            print(self.tokens)

            self.timestamp = self.parse_timestamp(self.tokens[0])

            print(self.tokens[1].text)
            if self.tokens[1].text.upper() in ("NAR", "COC"):
                self.process_narrative(data_store, datafile, change_id)
        else:
            # Not a line we recognise, so just skip to next one
            return

    def parse_timestamp(self, timestamp_token):
        timestamp_text = timestamp_token.text

        if timestamp_text[-1] != "Z":
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid format for timestamp - missing Z character: {timestamp_text}"
                }
            )
            return False

        try:
            day = int(timestamp_text[0:2])
            hour = int(timestamp_text[2:4])
            minute = int(timestamp_text[4:6])
        except ValueError:
            self.errors.append(
                {
                    self.error_type: f"Error on line {self.current_line_no}. "
                    f"Invalid format for timestamp - day, hour or min could not be converted to float: {timestamp_text}"
                }
            )
            return False

        return datetime(year=self.year, month=self.month, day=day, hour=hour, minute=minute)

    def process_narrative(self, data_store, datafile, change_id):
        comment_text = self.tokens[2].text
        print(f"Processing narrative with text: {comment_text}")

        platform = data_store.get_platform(platform_name=self.platform, change_id=change_id,)

        comment_type = data_store.add_to_comment_types("Narrative", change_id)

        comment = datafile.create_comment(
            data_store=data_store,
            platform=platform,
            timestamp=self.timestamp,
            comment=comment_text,
            comment_type=comment_type,
            parser_name=self.short_name,
        )

        self.last_entry = comment
