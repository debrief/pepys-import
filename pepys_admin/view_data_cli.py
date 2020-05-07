import cmd


class ViewDataShell(cmd.Cmd):
    intro = """--- Menu ---
    (1) View Data
    (2) Run SQL
    (0) Exit
    """
    prompt = "(pepys-admin) (view) "

    def __init__(self, data_store):
        super(ViewDataShell, self).__init__()
        self.data_store = data_store
        self.aliases = {
            "0": self.do_cancel,
            "1": self.do_view_data,
            "2": self.do_run_sql,
        }

    @staticmethod
    def do_cancel():
        print("Returning to the previous menu...")

    def do_view_data(self, option):
        pass

    def do_run_sql(self):
        pass

    def default(self, line):
        cmd_, arg, line = self.parseline(line)
        if cmd_ in self.aliases:
            self.aliases[cmd_]()
            if cmd_ == "0":
                return True
        else:
            print(f"*** Unknown syntax: {line}")

    def postcmd(self, stop, line):
        if stop is False:
            print("-" * 61)
            print(self.intro)
        return cmd.Cmd.postcmd(self, stop, line)
