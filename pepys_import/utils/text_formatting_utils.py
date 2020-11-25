from prompt_toolkit.formatted_text import FormattedText


def format_table(title: str, table_string: str):
    split_table = table_string.split("\n")
    title_text = ("", f"=={title}==\n")
    header_text = ("bold", split_table[0] + "\n")
    table_text = ("", "\n".join(split_table[1:]))
    formatted_text = FormattedText([title_text, header_text, table_text])
    return formatted_text


def format_menu(title, choices):
    return FormattedText([("bold", title), ("", choices)])


def format_command(text):
    return FormattedText([("bold", text)])
