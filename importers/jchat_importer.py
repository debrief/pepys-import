from dateutil.parser import parse as date_parse
from tqdm import tqdm

from pepys_import.core.validators import constants
from pepys_import.file.highlighter.xml_parser import parse
from pepys_import.file.importer import Importer
from pepys_import.utils.timezone_utils import TIMEZONE_MAPPINGS


class JChatImporter(Importer):
    """Imports JChat messages"""

    def __init__(self):
        super().__init__(
            name="JChat Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="JChat Importer",
            datafile_type="JChat",
        )

    def can_load_this_type(self, suffix):
        return suffix.upper() == ".HTML" or suffix == ""

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("<html>")

    def can_load_this_file(self, file_contents):
        # TODO: Decide how far we want to go with this check
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # JChat HTML is machine generated and appears to be well-formed
        # So we can use the XML parser
        try:
            doc = parse(path, highlighted_file=file_object)
        except Exception as e:
            self.errors.append(
                {
                    self.error_type: f'Invalid JChat file at {path}\nError from parsing was "{str(e)}"'
                }
            )
            return

        # TODO - Get the starting year / month from person importing
        self.year = 2021
        self.month = 10
        self.last_days = 0

        # Each chat message is wrapped in a <div> tag
        for div in tqdm(doc.findall(".//{*}div")):
            self._read_message_div(div, data_store, datafile, change_id)
            datafile.flush_extracted_tokens()

    def _read_message_div(self, div, data_store, datafile, change_id):
        """Reads the key parts of the JChat message from the data provided"""
        # TODO - doc comments
        msg_id = div.attrib["id"]  # TODO - do we need to record this?
        time_element = div.findall("{*}tt/font")
        if len(time_element) == 0:
            return  # TODO - record this as error
        time_string = time_element[0].text.strip("[").strip("]")
        print(time_string)
        timestamp = self.parse_timestamp(time_string, msg_id)

        platform_element = div.findall("{*}b/a/font")[0].text
        platform_quad = platform_element[0:4]
        print(platform_quad)
        # Match on quadgraphs
        platform = data_store.get_platform(quadgraph=platform_quad, change_id=change_id)
        print(platform.name)
        if platform is None:  # Couldn't get platform from quad
            platform = self.get_cached_platform(
                data_store, platform_name=platform_quad, change_id=change_id
            )

        msg_content_element = div.findall("{*}span/font//")
        # Message content may have <br> tags so need to handle
        # The <br/> tag splits the XML tree so we need to call text and tail
        # to make sure we get all the comment text
        msg_content_text = [part.text for part in msg_content_element if part.text is not None]
        msg_content_tails = [part.tail for part in msg_content_element if part.tail is not None]
        msg_content = str.join(" ", msg_content_text + msg_content_tails)

        comment = datafile.create_comment(
            data_store=data_store,
            platform=platform,
            timestamp=timestamp,
            comment=msg_content,
            comment_type=data_store.add_to_comment_types(
                "Narrative", change_id
            ),  # TODO - should this be "JChat" type?
            parser_name=self.short_name,
        )
        print(comment)

    def roll_month_year(self):
        """Rolls the current month/year over to the next one"""
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1

    def parse_timestamp(self, timestamp_str, msg_id):
        """Parses the JChat timestamp passed in for the given message
        :param timestamp_str: The DDHHmmssZ formatted date time string
        :param msg_id: The ID of the message whose timestamp is being parsed
        :return: Returns the parsed datetime representation of the timestamp
            OR False if unable to parse the timestamp
        :rtype: datetime | bool
        """
        if len(timestamp_str) != 9:
            self.errors.append(
                {self.error_type: f'Invalid JChat timestamp {timestamp_str} at {msg_id}"'}
            )
            return False
        # Parse days separately to make sure we have the right month/year
        days = int(timestamp_str[0:2])
        if days < self.last_days:
            self.roll_month_year()
        self.last_days = days

        return date_parse(f"{self.year}{self.month:02d}{timestamp_str}", tzinfos=TIMEZONE_MAPPINGS)
