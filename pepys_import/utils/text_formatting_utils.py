from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText

from pepys_import.utils.sqlite_utils import SYSTEM

WINDOWS = False
if SYSTEM == "Windows":  # pragma: no cover (tests only run on Linux)
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError  # pragma: no cover

    WINDOWS = True


def format_table(title: str, table_string: str):
    """Create a FormattedText object which has table headers in bold and normal style for the rest."""
    title_text = ("", f"=={title}==\n")
    split_table = table_string.split("\n")
    upper_lines = ("", split_table[0] + "\n")
    header_text = ("bold", split_table[1] + "\n")
    table_text = ("", "\n".join(split_table[2:]))
    formatted_text = FormattedText([title_text, upper_lines, header_text, table_text])
    return formatted_text


def format_menu(title: str, choices: str):
    """Create a FormattedText object which has title in bold and normal style for the choices."""
    return FormattedText([("#0e84b5 bold", title), ("#0e84b5", choices)])


def format_command(text):
    """Create a FormattedText object which makes the given text bold."""
    return FormattedText([("#0e84b5 bold", text)])


def formatted_text_to_str(formatted_text: FormattedText) -> str:
    """Converts FormattedText object to string"""
    str_text = ""
    for style, text in formatted_text:
        str_text += text
    return str_text


def custom_print_formatted_text(text):
    """Try to print using prompt toolkit's print_formatted_text().
    If it throws an error, Use the normal print function."""

    if not WINDOWS:
        print_formatted_text(text)
    else:
        try:
            print_formatted_text(text)
        # The following exception is expected when the application is not running inside a Windows Console
        # If that's the case, the program will use the normal print() function to print the outputs
        except NoConsoleScreenBufferError:
            print(formatted_text_to_str(text))
