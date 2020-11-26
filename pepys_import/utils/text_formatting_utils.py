from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.output.win32 import NoConsoleScreenBufferError


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
    return FormattedText([("bold", title), ("", choices)])


def format_command(text):
    """Create a FormattedText object which makes the given text bold."""
    return FormattedText([("bold", text)])


def custom_print_formatted_text(text):
    """Try to print using prompt toolkit's print_formatted_text().
    If it throws an error, Use the normal print function."""

    try:
        print_formatted_text(text)
    # The following exception is expected when the application is not running inside a Windows Console
    # If that's the case, the program will use the normal print() function to print the outputs
    except NoConsoleScreenBufferError:
        print(text)
