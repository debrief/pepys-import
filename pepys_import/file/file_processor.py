import os

from pepys_import.core.store.data_store import DataStore


class file_processor:
    def __init__(self):
        self.parsers = []

    def process(self, folder: str, data_store: DataStore, descending=True):
        """Process this folder of data
        
        :param folder: Folder path
        :type folder: String
        :param descending: Descend sub-folders, defaults to True
        :type descending: bool, optional
        """

        processed_ctr = 0

        # check folder exists
        if not os.path.isdir(folder):
            raise Exception("Folder not found: {}".format(folder))

        # make copy of list of parsers
        good_parsers = self.parsers.copy()

        filename, file_extension = os.path.splitext(folder)

        # loop through contents
        for filename in os.listdir(folder):

            # start with file suffxies
            tmp_parsers = good_parsers.copy()
            for parser in tmp_parsers:
                if not parser.can_accept_suffix(file_extension):
                    good_parsers.remove(parser)

            # now the filename
            tmp_parsers = good_parsers.copy()
            for parser in tmp_parsers:
                if not parser.can_accept_filename(filename):
                    good_parsers.remove(parser)

            # now the first line
            tmp_parsers = good_parsers.copy()
            for parser in tmp_parsers:
                if not parser.can_accept_first_line(filename):
                    good_parsers.remove(parser)

            # lastly the contents
            tmp_parsers = good_parsers.copy()
            for parser in tmp_parsers:
                if not parser.can_process_file(filename):
                    good_parsers.remove(parser)

            # ok, let these parsers handle the file
            for parser in good_parsers:
                parser.process()

    def register(self, parser):
        """Add this parser
        
        :param parser: new parser
        :type parser: core_parser
        """
        self.parsers.append(parser)
