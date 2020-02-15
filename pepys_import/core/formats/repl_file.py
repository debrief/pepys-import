from .state import State


# TODO: have base class to ensure filename and type are setup and returned
class REPFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.lines = []

        # TODO: it is not Pythonic way to use counter
        with open(filepath, "r") as file:
            line_number = 0
            for line in file:
                line_number += 1

                if len(line) == 0 or line[0] == ";":
                    continue

                repL = State(line_number, line)
                if not repL.parse():
                    raise Exception(
                        "failed parsing REP file {} line {}".format(
                            filepath, line_number
                        )
                    )

                self.lines.append(repL)

    def get_lines(self):
        return self.lines

    # TODO: could organise these values differently, eg. use registry of
    #  importers which also defines file type
    # although this works well for encapsulation
    @staticmethod
    def get_data_file_type():
        return "REP"

    def get_data_file_name(self):
        # TODO: should this be just the filename? or the full absolute or
        #  relative path supplied?
        return self.filepath
