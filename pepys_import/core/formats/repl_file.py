from pepys_import.core.formats.rep_line import REPLine


class REPFile:
    datafile_type = "REP"

    def __init__(self, filepath):
        self.filepath = filepath
        self.lines = []

        with open(filepath, "r") as file:
            for line_number, line in enumerate(file, 1):
                if len(line) == 0 or line[0] == ";":
                    continue

                rep_line = REPLine(line_number, line, " ")
                if not rep_line.parse():
                    raise Exception(f"failed parsing REP file {filepath} line {line_number}")
                self.lines.append(rep_line)
