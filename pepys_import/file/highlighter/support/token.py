from pepys_import.file.highlighter.level import HighlightLevel
from pepys_import.file.highlighter.support.utils import merge_adjacent_text_locations

from .usages import SingleUsage


class SubToken:
    """
    Object representing a single token at a lower level than Token.

    Usually there is a single SubToken object as a child of each Token object,
    but when tokens are combined (with the `combine_tokens` function) then
    there will be multiple SubToken children.

    Each SubToken object keeps track of the span (start and end characters) of the SubToken,
    the text that is contained within the SubToken, the character index that the line starts at
    and a reference to the overall character array created by HighlightedFile.
    """

    __slots__ = ("span", "text", "line_start", "chars")

    def __init__(self, span, text, line_start, chars):
        self.span = span
        self.text = text
        self.line_start = line_start
        self.chars = chars

    def start(self):
        """
        Returns the index into the character array that this SubToken starts at
        """
        return self.line_start + int(self.span[0])

    def end(self):
        """
        Returns the index into the character array that this SubToken ends at
        """
        return self.line_start + int(self.span[1])

    def __repr__(self):
        return "SubToken: (" + str(self.line_start) + "+" + repr(self.span) + ", " + self.text + ")"


class Token:
    """
    Object representing a single token extracted from a Line.

    This is the main object that the user will interact with, running
    the `record` method to record that this token has been used for a specific purpose.

    The `children` of this token are SubToken objects. Most of the time there will
    just be one SubToken object as a child of a Token object - however, when tokens are
    combined there can be multiple children.
    """

    __slots__ = ("children", "highlighted_file")

    def __init__(self, list_of_subtokens, hf_instance):
        """
        :param list_of_subtokens:  A list of SubToken objects
        to be kept as children of this object
        """
        self.children = list_of_subtokens
        self.highlighted_file = hf_instance

    def __repr__(self):
        res = "Token: "
        for child in self.children:
            res += "(" + str(child) + ")"
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

    @property
    def text_space_separated(self):
        """Returns the entire text of the Line, with spaces separating the different subtokens

        :return: Entire text content of the Line
        :rtype: String
        """
        return " ".join([child.text for child in self.children])

    def record(self, tool: str, field: str, value: str, units: str = None):
        """
        Record the usage of this token for a specific purpose

        :param tool: Name of the importer handling the import (eg. "NMEA Importer)
                     Should be set to `self.name` when called from an importer
        :param field: The field that the token is being interpreted as (eg. "speed")
        :param value: The parsed value of the token (eg. "5 knots") - where possible,
                      pass a Quantity object with associated units
        :param units: The units that the field was interpreted as using (optional - do not
                      include if the value was a Quantity as that holds unit information itself

        Technical details
        -----------------
        This adds SingleUsage objects to each of the relevant characters in the
        character array stored by the SubToken objects that are children of this object.
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

        usage = SingleUsage(tool_field, message)

        text_locations = []

        # This loop gives us each SubToken that is a child of this Token
        for subtoken in self.children:
            start = subtoken.start()
            end = subtoken.end()

            text_locations.append((start, end))

            for i in range(start, end):
                # Note: subtoken.chars is a reference to a single char array
                # that was originally created by the HighlightedFile class
                # So each time round the loop we're actually altering the same
                # char array, even though it is accessed via different SubToken
                # objects
                subtoken.chars[i].usages.append(usage)

        if recording_level == HighlightLevel.DATABASE:
            merged_text_locations = merge_adjacent_text_locations(text_locations)
            text_location_str = ",".join([f"{low}-{high}" for low, high in merged_text_locations])

            self.highlighted_file.datafile.pending_extracted_tokens.append(
                {
                    "text": self.text_space_separated,
                    "interpreted_value": str(value),
                    "text_location": text_location_str,
                    "importer": tool,
                    "field": field,
                }
            )
