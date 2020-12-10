import cmd

from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
    format_menu,
)


class BaseShell(cmd.Cmd):
    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        # Python accepts letters, digits, and "_" character as a command.
        # Therefore, "." is interpreted as an argument.
        if arg == "." and line == ".":
            self.aliases["."]()
            return True
        elif cmd_ in self.aliases:
            self.aliases[cmd_]()
        else:
            custom_print_formatted_text(format_error_message(f"*** Unknown syntax: {line}"))

    def get_title(self):
        title = getattr(self, "title", None)
        if not title:
            title = "--- Menu ---\n"
        return title

    def preloop(self):
        custom_print_formatted_text(format_menu(title=self.get_title(), choices=self.choices))

    def postcmd(self, stop, line):
        if line != ".":
            print("-" * 60)
            custom_print_formatted_text(format_menu(title=self.get_title(), choices=self.choices))
        return cmd.Cmd.postcmd(self, stop, line)
