from re import finditer

from .token import SubToken, Token
from .usages import SingleUsage


class Line:
    """
    Object representing a line from a HighlightedDatafile.

    Has methods to get a list of Tokens in the line, and to record a usage of the whole line.
    """

    WHITESPACE_DELIM = "\\S+"
    CSV_DELIM = r'(?:,"|^")(""|[\w\W]*?)(?=",|"$)|(?:,(?!")|^(?!"))([^,]*?)(?=$|,)|(\r\n|\n)'

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

    def tokens(self, reg_exp=WHITESPACE_DELIM, strip_char=""):
        """Generates a list of Token objects for each token in the line.
        
        :param reg_exp: Regular expression used to split the line into tokens. Useful
                        constants are defined in this class, including `CSV_DELIM`, defaults
                        to `WHITESPACE_DELIM`
        :type reg_exp: String, optional
        :param strip_char: Characters to strip after splitting, defaults to ""
        :type strip_char: String, optional
        :return: List of Token objects
        :rtype: List
        """
        tokens_array = []

        for child in self.children:
            for match in finditer(reg_exp, child.text):
                token_str = match.group()
                # special handling, we may need to strip a leading delimiter
                if strip_char != "":
                    char_index = token_str.find(strip_char)
                    if char_index == 0:
                        token_str = token_str[1:]
                        # and ditch any new whitespace
                    token_str = token_str.strip()

                subtoken = SubToken(match.span(), token_str, int(child.line_start), child.chars)

                # the token object expects an array of SubTokens, as it could be
                # a composite object
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
        # Don't record anything if the importer that called record
        # has called 'disable_recording()`
        if tool in self.highlighted_file.ignored_importers:
            return

        self.highlighted_file.fill_char_array_if_needed()

        tool_field = tool + "/" + field
        if units is not None:
            message = "Value:" + str(value) + " Units:" + str(units)
        else:
            message = "Value:" + str(value)

        for child in self.children:
            for i in range(int(child.start()), int(child.end())):
                usage = SingleUsage(tool_field, message)
                child.chars[i].usages.append(usage)
