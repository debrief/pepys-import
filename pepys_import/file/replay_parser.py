from .core_parser import core_parser


class replay_parser(core_parser):
    def __init__(self):
        super().__init__("Replay File Format")

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".REP" or suffix.upper() == ".DSF"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return True

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents):
        print("Rep parser working on " + path)
        pass
