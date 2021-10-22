from bs4 import BeautifulSoup

from pepys_import.core.validators import constants
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
        # Using beautifulsoup rather than the XML parser because JChat HTML is not
        # well-formed

        try:
            with open(path) as file:
                doc = BeautifulSoup(file, "html.parser")
        except Exception as e:
            self.errors.append(
                {
                    self.error_type: f'Invalid JChat file at {path}\nError from parsing was "{str(e)}"'
                }
            )
            return
        print("Divs:")
        divs = doc.find_all("div")
        for div in divs:
            msg_id = div["id"]
            print(msg_id)
            time_element = div.tt.font.contents[0].strip("[").strip("]")
            print(time_element)
            # TODO - parse time

            platform_element = div.a.font.contents[0]
            platform_quad = platform_element[0:4]
            print(platform_quad)
            # Match on quadgraphs
            platform = data_store.get_platform(quadgraph=platform_quad, change_id=change_id)
            print(platform.name)
            if platform is None:  # Couldn't get platform from quad
                platform = self.get_cached_platform(
                    data_store, platform_name=platform_quad, change_id=change_id
                )

            msg_content_element = div.i.contents[0].strip("[").strip("]")
            msg_content = msg_content_element.replace("<br/>", " ")
            print(msg_content)

        print("END Divs")
