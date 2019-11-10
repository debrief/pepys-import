from .core_parser import core_parser


class nmea_parser(core_parser):
    def __init__(self):
        super().__init__("NMEA File Format")

    def can_accept_suffix(self, suffix):
        return suffix.upper() == ".LOG" or suffix.upper() == ".TXT"

    def can_accept_filename(self, filename):
        return True

    def can_accept_first_line(self, first_line):
        return "$POSL" in first_line

    def can_process_file(self, file_contents):
        return True

    def process(self, data_store, path, file_contents, datafile):
        print("NMEA parser working on " + path)
        pass
