from .state import State


class REPFile:
    datafile_type = "REP"

    def __init__(self, filepath):
        self.filepath = filepath
        self.lines = []

        with open(filepath, "r") as file:
            for line_number, line in enumerate(file):
                if len(line) == 0 or line[0] == ";":
                    continue

                rep_line = State(line_number + 1, line)
                if not rep_line.parse():
                    raise Exception(
                        f"failed parsing REP file {filepath} line {line_number+1}"
                    )
                self.lines.append(rep_line)
