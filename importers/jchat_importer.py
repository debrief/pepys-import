import os
import re
from datetime import datetime

from dateutil.tz import tzoffset
from lxml import etree, html
from tqdm import tqdm

from pepys_import.core.validators import constants
from pepys_import.file.highlighter.xml_parser import parse
from pepys_import.file.importer import Importer
from pepys_import.utils.timezone_utils import TIMEZONE_MAPPINGS

# In future, we may be able to replace these with actual version numbers
JCHAT_LEGACY = 1
JCHAT_MODERN = 2


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
        if header:
            return header.startswith("<html>")
        return False

    def can_load_this_file(self, file_contents):
        if len(file_contents) < 8:  # Enough to cover the header
            return False
        # Check the HTML header
        is_valid = "html" in file_contents[0]
        is_valid = is_valid and "head" in file_contents[1]
        is_valid = is_valid and 'style type="text/css"' in file_contents[2]
        # Only going to check for msgcontent in case there are other styles
        is_valid = is_valid and "msgcontent" in "".join(file_contents[3:8])
        return is_valid

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        # JChat HTML is machine generated but <br> and <hr> tags are not valid
        # XML and appear in several of the example files, so load & correct to xml
        with open(path) as original:
            original_doc = original.read()
            simplified_doc = html.fromstring(self.simplify_jchat_html(original_doc))

        xhtml_path = f"{path}.xhtml"
        with open(xhtml_path, "wb") as corrected:
            corrected.write(etree.tostring(simplified_doc))

        file_object.reinitialise(xhtml_path, datafile)
        try:
            doc = parse(xhtml_path, highlighted_file=file_object)
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
            data_store.ask_for_missing_info(
                "Which year was this file generated (YYYY)?",
                default_value=self.year,
                min_value=1990,
                allow_empty=True,
            )
        )
        self.month = int(
            data_store.ask_for_missing_info(
                "Which month was this file generated (MM)?",
                default_value=self.month,
                min_value=1,
                max_value=12,
                allow_empty=True,
            )
        )

        # Each chat message is wrapped in a <div> tag
        for div in tqdm(doc.findall(".//{*}div")):
            self._read_message_div(div, data_store, datafile, change_id)

        try:
            # Delete the extra file
            os.remove(xhtml_path)
        except IOError:
            self.errors.append(
                {
                    self.error_type: f'Unable to remove intermediate file at {xhtml_path}\nPlease delete this file manually."'
                }
            )

    def _read_message_div(self, div, data_store, datafile, change_id):
        """Reads the key parts of the JChat message from the data provided
        :param div: The div tag from the JChat message to parse
        :param data_store: The data store we're putting this message into
        :param datafile: The data file we're extracting from
        :param change_id: The change ID of this import
        """
        try:
            # Older format uses id=
            # Newer format uses msgid=
            msg_id = div.attrib["msgid"]  # Grabbing ID to help with error reporting
        except KeyError:
            try:
                msg_id = div.attrib["id"]
            except KeyError:
                # Ignore any non-comment messages (e.g. connect/disconnect)
                return

        # Sample data included some "Marker" messages with the id="marker"
        if str.upper(msg_id) == "MARKER":
            return  # Ignore these messages

        text_blocks = []
        text_blocks.append([item for item in div.findall(".//*") if item.text])
        if text_blocks[0]:
            time_element = text_blocks[0][0]
            platform_element = text_blocks[0][1]
            msg_content_element = text_blocks[0][2:]

        if not text_blocks[0] or len(text_blocks[0]) < 3:
            self.errors.append(
                {
                    self.error_type: f"Unable to read message {msg_id}. Not enough parts (expecting timestamp, platform, message)"
                }
            )
            return

        time_string = time_element.text.strip("[").strip("]")
        timestamp = self.parse_timestamp(time_string, msg_id)
        time_element.record(self.name, "timestamp", timestamp)

        platform_quad = platform_element.text[0:4]
        platform_element.record(self.name, "platform", platform_quad)
        # Match on quadgraphs
        platform = self.get_cached_platform_from_quad(data_store, platform_quad, change_id)

        msg_content = self.parse_message_content(msg_content_element)

        if not msg_content:
            self.errors.append({self.error_type: f"Unable to parse JChat message {msg_id}."})
            return
        msg_content_element[0].record(self.name, "Content", msg_content)

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
                {self.error_type: f"Invalid JChat timestamp {timestamp_str} at {msg_id}"}
            )
            return False
        # Parse days separately to make sure we have the right month/year
        days = int(timestamp_str[0:2])
        if days < self.last_days:
            self.roll_month_year()
        self.last_days = days

        day_and_time = timestamp_str[0:8]
        timezone_offset = TIMEZONE_MAPPINGS[timestamp_str[8]]

        timezone_aware_timestamp = datetime.strptime(
            f"{self.year}{self.month:02d}{day_and_time}{timezone_offset}", "%Y%m%d%H%M%S%z"
        )
        # Give back the time in UTC for storing
        return timezone_aware_timestamp.astimezone(tzoffset("UTC", 0))

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
            data_store, platform_name=platform_name, quadgraph=quadgraph, change_id=change_id
        )
        # Got a platform name, so now cache it
        self.quad_platform_cache[quadgraph] = platform_name

        return platform

    def parse_message_content(self, msg_content_element):
        """Takes the content of a JChat message and parses it to a string
        :param msg_content_element: The XML element with the message in it
        :ptype msg_content_element: Element
        :return: The message content text
        :rtype: String
        """
        if not msg_content_element:
            return None
        msg_content = " ".join([text for text in msg_content_element[0].itertext()])
        msg_content = re.sub(" +", " ", msg_content.replace("\n", "").strip())
        try:
            cp1252_content = msg_content.encode("cp1252", "ignore").decode("cp1252", "ignore")
            return cp1252_content
        except UnicodeError:
            return None

    @staticmethod
    def simplify_jchat_html(jchat_html_string):
        """Strips tags that are common in jchat files but get in the way of parsing
        :param jchat_html_string: The jchat HTML
        :ptype jchat_html_string: String
        :returns: The original string without the awkward tags"""
        # The (tag to remove, string to replace it with)
        tags_to_remove = [
            ("<i>", ""),
            ("</i>", ""),
            ("<br>", " "),
            ("<br/>", " "),
            ("</br>", ""),  # Avoid double space
            ('<span class="msgcontent">', ""),
            ("<span>", ""),
            ("</span>", ""),
        ]
        simple_html_string = jchat_html_string
        for tag, replacement in tags_to_remove:
            simple_html_string = simple_html_string.replace(tag, replacement)

        return simple_html_string
