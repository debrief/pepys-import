from tqdm import tqdm

from pepys_import.file.highlighter.support.line import Line

from ...utils.text_formatting_utils import custom_print_formatted_text, format_error_message
from .support.char import Char
from .support.export import export_report
from .support.token import SubToken


class HighlightedFile:
    """
    class that can load/tokenize a datafile, record changes to the file,
    then export a highlighted version of the file that indicates extraction
    """

    def __init__(self, filename: str, datafile=None, number_of_lines=None):
        """
        Constructor for this object
        Args:
            filename (str): The name of the file to be parsed/reported upon
            number_of_lines(int) Number of lines that should be shown
                   in the output (all lines if None)
        """
        self.chars = []
        self.filename = filename
        self.dict_color = {}
        self.number_of_lines = number_of_lines
        self.datafile = datafile

        self.importer_highlighting_levels = {}

    def chars_debug(self):
        """
        Debug method, to check contents of chars
        """
        self.fill_char_array_if_needed()
        return self.chars

    def lines(self):
        """
        Slice the file into lines and return a list of Line objects
        """
        if self.number_of_lines is None:
            return self.not_limited_lines()
        elif self.number_of_lines <= 0:
            custom_print_formatted_text(
                format_error_message("Non-positive number of lines. Please provide positive number")
            )
            exit(1)
        else:
            return self.limited_lines()

    def export(self, filename: str, include_key=False):
        """
        Provide highlighted summary for this file
        Args:
        filename (str): The name of the destination for the HTML output
        include_key (bool): Whether to include a key at the bottom of the output
        showing what each colour refers to
        """
        if len(self.chars) > 0:
            export_report(filename, self.chars, self.dict_color, include_key)

    def limited_contents(self):
        with open(self.filename, "r") as file:
            whole_file_contents = file.read()

        lines_list = whole_file_contents.splitlines()

        lines_list = lines_list[0 : self.number_of_lines]
        limited_contents = "\n".join(str(e) for e in lines_list)

        return limited_contents, lines_list

    def limited_lines(self):
        """
        Return a list of Line objects for each line in the file,
        producing only self.number_of_lines objects (to limit length
        of output for very large files)
        """

        limited_contents, lines_list = self.limited_contents()

        lines = self.create_lines(limited_contents, lines_list)
        return lines

    def not_limited_lines(self):
        """
        Return a list of Line objects for each line in the file
        """
        with open(self.filename, "r") as file:
            file_contents = file.read()

        lines_list = file_contents.splitlines()
        lines = self.create_lines(file_contents, lines_list)

        return lines

    def fill_char_array_if_needed(self):
        if len(self.chars) > 0:
            # Char array already filled, so no need to do anything
            return

        if self.number_of_lines is None:
            with open(self.filename, "r") as file:
                file_contents = file.read()
        elif self.number_of_lines <= 0:
            raise ValueError("Non-positive number of lines. Please provide positive number")
        else:
            file_contents, _ = self.limited_contents()

        # We need to store the contents of the file as bytes so that
        # the record call on an XML element can convert from bytes offsets to character offsets
        with open(self.filename, "rb") as f:
            self.file_byte_contents = f.read()

        # Initialise the char index (self.chars), with one Char entry for
        # each character in the file. (Note: a reference to this char array is
        # given to each SubToken)
        # We do this as a list comprehension as it's more efficient, but we have to
        # add it to list that already exists in self.chars, as references have already
        # been made to this list
        self.chars += [Char(c) for c in tqdm(file_contents)]

    def set_usages_for_slice(self, start, end, usage):
        for i in range(start, end):
            self.chars[i].usages.append(usage)

        return (start, end)

    def create_lines(self, file_contents, lines_list):
        """
        Create individual Line objects
        for each line, with appropriate references to the character array
        """
        # Keeps track of which character in the file a line starts on
        line_start_counter = 0
        lines = []

        # For each line in the file create a Line object with a SubToken
        # object as its child, keeping track of the length of the line
        # and which character of the file this line starts on
        for this_line in lines_list:
            line_length = len(this_line)
            line_span = (0, len(this_line))
            # Create SubToken object to keep track of the line length, the line itself
            # the start character of the line in the file, and a reference to the overall
            # list of characters
            sub_token = SubToken(line_span, this_line, int(line_start_counter), self.chars)
            new_l = Line([sub_token], self)
            lines.append(new_l)
            # Update the starting character of the line ready for next time
            line_start_counter += line_length + 1

        return lines
