from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.support.char import Char
from pepys_import.file.highlighter.support.line import Line
from pepys_import.file.highlighter.support.token import SubToken


def create_test_line_object(line_str):
    """
    Create a Line object for the given string, with all of the various member
    variables set properly, so it can be passed to something expecting a line
    and work.

    Used for tests, particularly of the REP line parser
    """
    # Create a highlighted file object but with no filename attached
    test_hf = HighlightedFile(None)

    # Fill the chars array manually
    for char in line_str:
        char_obj = Char(char)
        test_hf.chars.append(char_obj)

    # Create a line object ready to return
    line_span = (0, len(line_str))
    sub_token = SubToken(line_span, line_str, 0, test_hf.chars)
    new_line = Line([sub_token], test_hf)

    return new_line


class FakeDatafile:
    def __init__(self):
        self.pending_extracted_tokens = []


def delete_entries(d, keys_to_delete):
    for key in keys_to_delete:
        del d[key]

    return d
