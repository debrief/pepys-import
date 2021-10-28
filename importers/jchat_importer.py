import io
from datetime import datetime

from dateutil.parser import parse as date_parse
from lxml import etree, html
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
        self.year = datetime.now().year
        self.month = datetime.now().month
        self.last_days = 0

    def can_load_this_type(self, suffix):
        # The sample data that we have includes some files with .html but
        # several files have no extension and have a . in the name
        # so we can't use the file extension
        return True

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return header.startswith("<html>")

    def can_load_this_file(self, file_contents):
        # TODO: Decide how far we want to go with this check
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # JChat HTML is machine generated but <br> and <hr> tags are not valid
        # XML and appear in several of the example files, so load & correct to xml
        with open(path) as original:
            original_doc = html.fromstring(original.read())
        corrected = io.BytesIO(etree.tostring(original_doc))

        try:
            doc = parse(corrected, highlighted_file=file_object)
        except Exception as e:
            self.errors.append(
                {
                    self.error_type: f'Invalid JChat file at {path}\nError from parsing was "{str(e)}"'
                }
            )
            print(f"Error {e}")
            return

        self.quad_platform_cache = {}
        self.year = int(
            data_store.ask_for_missing_info("Which year was this file generated (YYYY)?", self.year)
        )
        self.month = int(
            data_store.ask_for_missing_info("Which month was this file generated (MM)?", self.month)
        )
        # TODO - Check these are valid year/month (ideally on input)

        # Each chat message is wrapped in a <div> tag
        for div in tqdm(doc.findall(".//{*}div")):
            self._read_message_div(div, data_store, datafile, change_id)

    def _read_message_div(self, div, data_store, datafile, change_id):
        """Reads the key parts of the JChat message from the data provided
        :param div: The div tag from the JChat message to parse
        :param data_store: The data store we're putting this message into
        :param datafile: The data file we're extracting from
        :param change_id: The change ID of this import
        """
        try:
            msg_id = div.attrib["id"]  # Grabbing ID to help with error reporting
        except KeyError:
            # Ignore any non-comment messages (e.g. connect/disconnect)
            return
        time_element = div.findall("{*}tt/font")
        if len(time_element) == 0:
            return  # TODO - record this as error
        time_string = time_element[0].text.strip("[").strip("]")
        timestamp = self.parse_timestamp(time_string, msg_id)
        time_element[0].record(self.name, "timestamp", timestamp)

        platform_element = div.findall("{*}b/a/font")[0]
        platform_quad = platform_element.text[0:4]
        platform_element.record(self.name, "platform", platform_quad)
        # Match on quadgraphs
        platform = self.get_cached_platform_from_quad(data_store, platform_quad, change_id)

        msg_content_element = div.findall("{*}span/font//")
        # Message content may have <br> tags so need to handle
        # The <br/> tag splits the XML tree so we need to call text and tail
        # to make sure we get all the comment text
        msg_content_text = [part.text for part in msg_content_element if part.text is not None]
        msg_content_tails = [part.tail for part in msg_content_element if part.tail is not None]
        msg_content = str.join(" ", msg_content_text + msg_content_tails)

        try:
            # Try encoding to avoid issues with highlighter
            msg_content_element[0].record(self.name, "Content", msg_content.encode("cp1252"))
        except Exception as e:
            print(f"Unicode error: {e.object}")

        datafile.create_comment(
            data_store=data_store,
            platform=platform,
            timestamp=timestamp,
            comment=msg_content,
            comment_type=data_store.add_to_comment_types("JChat", change_id),
            parser_name=self.short_name,
        )

        datafile.flush_extracted_tokens()

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
        :return: The parsed datetime representation of the timestamp
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

    def get_cached_platform_from_quad(self, data_store, quadgraph, change_id):
        """Attempts to get a platform from the quadgraph
        :param data_store: The data store that we want to get the platform from
        :param quadgraph: The quadgraph to get a platform for
        :param change_id: The change ID should we need to make a new platform
        :return: The platform for this quadgraph
        :rtype: Platform
        """
        # look in the cache first
        platform_name = self.quad_platform_cache.get(quadgraph)
        if platform_name is None:
            # Otherwise we need to check whether there is actually a platform with this quad
            platform_name = data_store.get_platform_name_from_quad(quadgraph)
            if platform_name is None:
                platform_name = quadgraph

        # Grab the right platform
        platform = self.get_cached_platform(
            data_store, platform_name=platform_name, change_id=change_id
        )
        # Got a platform name, so now cache it
        self.quad_platform_cache[quadgraph] = platform_name

        return platform
