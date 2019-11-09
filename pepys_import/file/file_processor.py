class file_processor:
    def __init__(self):
        self.parsers = []

    def process(self, folder, descending=True):
        # check folder exists

        # loop through contents

        # loop through parser
        for parser in self.parsers:
            print(parser)

    def register(self, parser):
        self.parsers.append(parser)
