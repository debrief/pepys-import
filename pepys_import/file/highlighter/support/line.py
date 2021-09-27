from re import finditer, search

from pepys_import.file.highlighter.support.utils import merge_adjacent_text_locations
from pepys_import.file.highlighter.level import HighlightLevel

from .token import SubToken, Token
from .usages import SingleUsage


class Line:
    """
    Object representing a line from a HighlightedDatafile.

    Has methods to get a list of Tokens in the line, and to record a usage of the whole line.
    """

    WHITESPACE_TOKENISER = "\\S+"
    CSV_TOKENISER = r'(?:,"|^")(""|[\w\W]*?)(?=",|"$)|(?:,(?!")|^(?!"))([^,]*?)(?=$|,)|(\r\n|\n)'
    QUOTED_NAME_REGEX = r"([\"'])(?:(?=(\\?))\2.)*?\1"

    __slots__ = ("children", "highlighted_file")

    def __init__(self, list_of_subtokens, hf_instance):
        """
        Create a new line, giving it a list of SubToken objects as children of the line

        Usually this will be just a list of one item, but has the flexibility to have more
        for composite tokens.
        """
        self.children = list_of_subtokens
        self.highlighted_file = hf_instance

    def __repr__(self):
        res = "Line: "
        for child in self.children:
            res += "(" + str(child.line_start) + "+" + repr(child.span) + ", " + child.text + ")"
        return res

    @property
    def text(self):
        """Returns the entire text of the Line

        :return: Entire text content of the Line
        :rtype: String
        """
        res = ""
        for child in self.children:
            res += child.text
        return res

    def tokens(self, reg_exp=WHITESPACE_TOKENISER, strip_char="", quoted_name=QUOTED_NAME_REGEX):
        """Generates a list of Token objects for each token in the line.

        :param reg_exp: Regular expression used to split the line into tokens. Useful
                        constants are defined in this class, including `CSV_TOKENISER`, defaults
                        to `WHITESPACE_TOKENISER`. See notes below.
        :type reg_exp: String, optional
        :param strip_char: Characters to strip after splitting, defaults to ""
        :type strip_char: String, optional
        :return: List of Token objects
        :rtype: List

        Notes:
        The reg_exp given to this function should be a regular expression that extracts the individual tokens from the line,
        and *not* a regular expression that identifies the characters to split by. Thus, the WHITESPACE_TOKENISER regex is
        simply \\S+, which matches any amount of anything that isn't whitespace. The CSV_TOKENISER is more complex, as it deals
        with quotes and other issues that cause problems in CSV files.
        The regular expression can use groups, but the entire match of the regular expression should be the token - there is no
        capacity (currently at least) for extracting particular groups of the regular expression. Use can be made of look-ahead
        and look-behind expressions in the regex to constrain it so that the entire match covers just the token and nothing else.
        (For a good example of this see the SLASH_TOKENISER in the Nisida importer)
        """
        tokens_array = []

        for child in self.children:
            # Search and match values between quotation marks if there is any
            quoted_text_match = search(quoted_name, child.text)
            start, end = None, None
            if quoted_text_match:
                original_name = quoted_text_match.group()
                start, end = quoted_text_match.span()
                # Remove quotation marks and then strip the text
                quoted_sensor_name = original_name[1:-1].strip()
                subtoken_sensor_name = SubToken(
                    (start, end), quoted_sensor_name, int(child.line_start), child.chars
                )
                subtokens_sensor_name = [subtoken_sensor_name]

            for match in finditer(reg_exp, child.text):
                token_str = match.group()
                token_start, token_end = match.span()
                # If quoted text exists and it contains the split token, continue or
                # add the quoted text's Token object
                if start and end and token_start >= start and token_end <= end:
                    # Since quoted text might contain a few tokens and it should be added to the
                    # token arrays in the correct position, the following if clause used. It adds
                    # the quoted text if token's end is equal to the quoted text's end.
                    if token_end == end:
                        tokens_array.append(Token(subtokens_sensor_name, self.highlighted_file))
                    continue

                # special handling, we may need to strip a leading delimiter
                if strip_char != "":
                    char_index = token_str.find(strip_char)
                    if char_index == 0:
                        token_str = token_str[1:]
                        token_start += 1
                    # and ditch any new whitespace
                    token_str = token_str.strip()

                subtoken = SubToken(
                    (token_start, token_end), token_str, int(child.line_start), child.chars
                )
                # the token object expects an array of SubTokens, as it could be a composite object
                list_of_subtokens = [subtoken]
                tokens_array.append(Token(list_of_subtokens, self.highlighted_file))

        return tokens_array

    def record(self, tool: str, field: str, value: str, units: str = None):
        """
        Record a usage of the whole line

        :param tool: Name of the importer handling the import (eg. "NMEA Importer)
                     Should be set to `self.name` when called from an importer
        :param field: The field that the token is being interpreted as (eg. "speed")
        :param value: The parsed value of the token (eg. "5 knots") - where possible,
                      pass a Quantity object with associated units
        :param units: The units that the field was interpreted as using (optional - do not
                      include if the value was a Quantity as that holds unit information itself

        Technical details:
        ------------------
        Adds a SingleUsage object to each of the relevant characters in the
        char array referenced by each SubToken child.
        """
        recording_level = self.highlighted_file.importer_highlighting_levels.get(tool, None)
        if recording_level == HighlightLevel.NONE:
            return

        self.highlighted_file.fill_char_array_if_needed()

        tool_field = tool + "/" + field
        if units is not None:
            message = "Value:" + str(value) + " Units:" + str(units)
        else:
            message = "Value:" + str(value)

        text_locations = []

        for child in self.children:
            start = child.start()
            end = child.end()

            text_locations.append((start, end))

            for i in range(start, end):
                usage = SingleUsage(tool_field, message)
                child.chars[i].usages.append(usage)

        if recording_level == HighlightLevel.DATABASE:
            merged_text_locations = merge_adjacent_text_locations(text_locations)
            text_location_str = ",".join([f"{low}-{high}" for low, high in merged_text_locations])

            self.highlighted_file.datafile.pending_extracted_tokens.append(
                {
                    "text": self.text,
                    "interpreted_value": str(value),
                    "text_location": text_location_str,
                    "importer": tool,
                    "field": field,
                }
            )
