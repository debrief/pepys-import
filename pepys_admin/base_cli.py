import cmd


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
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if line != ".":
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
