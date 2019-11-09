from .core_parser import core_parser


class sample_parser(core_parser):
    def can_accept_suffix(self, suffix):
        return suffix == "rep"

    def can_accept_filename(self, filename):
        return "good_file" in filename

    def can_accept_first_line(self, first_line):
        return "good" in first_line

    def can_process_file(self, file_contents):
        return "good" in file_contents

    def process(self, data_store, file_contents):
        pass
