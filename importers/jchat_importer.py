from datetime import datetime

from pepys_import.core.validators import constants
from pepys_import.file.highlighter.xml_parser import parse
from pepys_import.file.importer import Importer


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

        # TODO - Get the Year / month from person importing

        print("Divs:")
        divs = doc.findall(".//{*}div")
        for div in divs:
            msg_id = div.attrib["id"]
            print(msg_id)
            time_element = div.findall("{*}tt/font")[0].text.strip("[").strip("]")
            print(time_element)
            timestamp = self.parse_timestamp(time_element)

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

            msg_content_element = div.findall("{*}span/font/i")[0].text.strip("[").strip("]")
            msg_content = msg_content_element.replace("<br/>", " ")
            print(msg_content)

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
            datafile.flush_extracted_tokens()
        # TODO - handle Token creation

        print("END Divs")

    @staticmethod
    def parse_timestamp(timestamp_str):
        return datetime(2021, 5, 6, 1, 2, 3)
