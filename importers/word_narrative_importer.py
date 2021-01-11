import os
import re
from datetime import datetime
from xml.etree.ElementTree import XML

from docx import Document

from pepys_import.core.validators import constants
from pepys_import.file.importer import Importer

WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
TEXT = WORD_NAMESPACE + "t"


class WordNarrativeImporter(Importer):
    def __init__(self):
        super().__init__(
            name="Word Narrative Format Importer",
            validation_level=constants.BASIC_LEVEL,
            short_name="Word Narrative Importer",
            default_privacy="Public",
            datafile_type="Word Narrative",
        )

        self.last_day = None
        self.last_month = None
        self.last_year = None

    def can_load_this_type(self, suffix):
        return suffix.upper() in [".DOCX", ".PDF"]

    def can_load_this_filename(self, filename):
        return True

    def can_load_this_header(self, header):
        return True

    def can_load_this_file(self, file_contents):
        return True

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        print("Loading file")
        _, ext = os.path.splitext(path)
        if ext.upper() == ".DOCX":
            header, entries, error = self.load_docx_file(path)
        elif ext.upper() == ".PDF":
            header, entries, error = self.load_pdf_file(path)
        else:
            self.errors.append({self.error_type: f"Unsupported file extension {ext}."})
            return

        if error:
            # Stop parsing if there was an error during loading that we can't recover from
            return

        self.parse_file(header, entries, data_store, change_id)

    def parse_file(self, header, entries, data_store, change_id):
        platform = self.get_cached_platform(
            data_store, platform_name=header["platform"], change_id=change_id
        )
        print(platform)

        # Loop through each entry in the file
        for entry in entries:
            print(f"Entry {entry}")
            parts = entry.strip().split(",")

            correct_length = len(parts) > 5
            has_four_fig_datetime = correct_length and re.fullmatch(r"\d{4}", parts[0])
            has_six_fig_datetime = correct_length and re.fullmatch(r"\d{6}", parts[0])

            has_datetime = has_four_fig_datetime or has_six_fig_datetime

            if has_datetime:
                # Parse datetime
                timestamp, error = self.parse_datetime(parts, four_fig=has_four_fig_datetime)
                if error:
                    continue

                # Process rest of entry
                entry_platform_name = parts[4].strip()

                if entry_platform_name != header["platform"]:
                    header_platform_name = header["platform"]
                    self.errors.append(
                        {
                            self.error_type: f"Platform name in entry ('{entry_platform_name}') doesn't match platform name in header ('{header_platform_name}')"
                        }
                    )
                    continue

                message_type = parts[5].strip()

                if len(message_type) > 20:
                    # Sometimes there isn't the end comma on the message type field
                    # which means it gets merged with the text field
                    # If this field is very long then this is probably what happened
                    # So we find the first location of a tab, and split on that
                    index = message_type.find("\t")
                    if index != -1:
                        text = message_type[index:].strip()
                        message_type = message_type[:index].strip()
                    else:
                        fulltext = ",".join(parts)
                        self.errors.append(
                            {
                                self.error_type: f"Can't separate message type and text, are fields mangled or a comma missing? {fulltext}"
                            }
                        )
                    continue
                else:
                    text = ",".join(parts[6:]).strip()

                print(f"Timestamp: {timestamp}")
                print(f"message_type: {message_type}")
                print(f"text: {text}")
            else:
                # Append to previous entry
                pass

    def parse_datetime(self, parts, four_fig):
        day_visible = None

        # Get the parts separated by commas, as they're always there
        day_hidden = int(parts[1])
        month = int(parts[2])
        year = int(parts[3])

        if four_fig:
            # It's a four figure time with just HHMM
            hour = int(parts[0][0:2])
            mins = int(parts[0][2:4])
        else:
            # It's a six figure time with DDHHMM
            day_visible = int(parts[0][0:2])  # day in the visible text
            hour = int(parts[0][2:4])
            mins = int(parts[0][4:6])

            # Deal with entries that might need to be pulled back from the next day
            # If something that happened at 2345 only gets entered at 0010 then
            # the hidden text will have the next day in it, when it should be
            # the previous day
            if hour == 23:
                if day_hidden == day_visible + 1:
                    day_hidden = day_visible

            if day_hidden != day_visible:
                full_text = ",".join(parts)
                self.errors.append(
                    {
                        self.error_type: f"Day in text doesn't match day in hidden text - possible copy/paste error: '{full_text}'."
                    }
                )
                return None, True

        day = day_visible or day_hidden

        day_decreased = (self.last_day is not None) and (day < self.last_day)
        month_increased = (self.last_month is not None) and (month > self.last_month)
        year_increased = (self.last_month is not None) and (year > self.last_year)

        # Deal with entries where the day has decreased (ie. gone to the beginning of the next month)
        # but the month and/or year hasn't increased
        # This suggests that there has been a copy-paste error, mangling the data
        if day_decreased and ((not month_increased) or (not year_increased)):
            self.errors.append(
                {self.error_type: f"Day decreased but month/year didn't increase: {parts[0]}."}
            )
            return None, True
        else:
            # Everything makes sense, so we can update the last_X variables
            self.last_day = day_visible
            self.last_month = month
            self.last_year = year

        if year < 100:
            # If a two digit year
            if year > 80:
                # If it is from 80s onwards then it's 1900s
                year = 1900 + year
            else:
                year = 2000 + year

        if year < 1900 or year > 2100:
            self.errors.append({self.error_type: f"Year too big or too small: {year}."})
            return None, True

        try:
            timestamp = datetime(year, month, day, hour, mins)
        except ValueError:
            full_text = ",".join(parts)
            self.errors.append({self.error_type: f"Could not parse timestamp {full_text}."})
            return None, True

        return timestamp, False

    def load_docx_file(self, path):
        try:
            doc = Document(path)
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Invalid docx file at {path}\nError from parsing was "{str(e)}"'}
            )
            return None, None, True

        try:
            # Get text from the header
            # Headers are attached to a document section, so we need to extract the section first
            sec = doc.sections[0]
            header_text = ""
            for para in sec.header.paragraphs:
                header_text += "\n" + para.text

            splitted = re.split("[\n\t]+", header_text.strip())
            header = {}
            header["privacy"] = splitted[0].strip()
            header["platform"] = splitted[1].strip()
            header["exercise"] = splitted[4].strip()
            header["fulltext"] = header_text.strip()
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Cannot extract header\nError from parsing was "{str(e)}"'}
            )
            return None, None, True

        try:
            # Get each paragraph entry, after accepting any tracked changes
            entries = []
            for p in doc.paragraphs:
                entries.append(self.get_accepted_text(p))
        except Exception as e:
            self.errors.append(
                {self.error_type: f'Cannot extract paragraphs\nError from parsing was "{str(e)}"'}
            )
            return None, None, True

        return header, entries, False

    def get_accepted_text(self, p):
        """Return text of a paragraph after accepting all changes.

        This gets the XML content of the paragraph and checks for deletions or insertions. If there
        aren't any, then it just returns the text. If there are some, then it parses the XML and
        joins the individual text entries."""
        # Taken from https://stackoverflow.com/questions/38247251/how-to-extract-text-inserted-with-track-changes-in-python-docx
        xml = p._p.xml
        if "w:del" in xml or "w:ins" in xml:
            tree = XML(xml)
            runs = (node.text for node in tree.iter(TEXT) if node.text)
            return "".join(runs)
        else:
            return p.text
