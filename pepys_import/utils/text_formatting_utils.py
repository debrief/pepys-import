import textwrap

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


def format_error_menu(title: str, choices: str):
    """Create a FormattedText object which has title in red and normal style for the choices."""
    return FormattedText([("#dc3545", title), ("", choices)])


def format_command(text):
    """Create a FormattedText object which makes the given text bold."""
    return FormattedText([("#0e84b5 bold", text)])


def format_help_text(text):
    """Create a FormattedText object which makes the given text blue."""
    return FormattedText([("#28a745", text)])


def format_error_message(text):
    """Create a FormattedText object which makes the given text red."""
    return FormattedText([("#dc3545", text)])


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
        try:
            print_formatted_text(text)
        except TypeError:
            print(formatted_text_to_str(text))
    else:
        try:
            print_formatted_text(text)
        # The following exception is expected when the application is not running inside a Windows Console
        # If that's the case, the program will use the normal print() function to print the outputs
        except NoConsoleScreenBufferError:
            print(formatted_text_to_str(text))


def print_new_section_title(text, line_width=60):
    lines = wrap_text(text, line_width - 10)
    lines = [f"#{line.center(line_width-2)}#" for line in lines]
    lines.insert(0, "\n" + "#" * line_width)
    lines.append("#" * line_width)
    lines.append("Type HELP or ? at any time to display contextual help.")
    print(*lines, sep="\n")


def wrap_text(text, line_width=60):
    return textwrap.wrap(text, line_width)


def print_help_text(data_store, help_id):
    HelpText = data_store.db_classes.HelpText
    help_text = data_store.session.query(HelpText).filter(HelpText.id == help_id).first()
    if help_text:
        print("-" * 60)
        lines = wrap_text(help_text.guidance)
        lines.append(f"({help_id})")
        wrapped_text = "\n".join(lines)
        custom_print_formatted_text(format_help_text(wrapped_text))
        input("<Press Enter to continue>")
