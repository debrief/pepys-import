import os

from pepys_import.core.store.data_store import DataStore


class file_processor:
    def __init__(self):
        self.parsers = []

    def process(self, folder: str, data_store: DataStore):
        """Process this folder of data
        
        :param folder: Folder path
        :type folder: String
        :param data_Store: Database
        :type data_store: DataStore
        """

        processed_ctr = 0

        # check folder exists
        if not os.path.isdir(folder):
            raise Exception("Folder not found: {}".format(folder))

        # make copy of list of parsers
        good_parsers = self.parsers.copy()

        filename, file_extension = os.path.splitext(folder)

        # capture path in absolute form
        abs_path = os.path.abspath(folder)

        # loop through contents
        for currentpath, folders, files in os.walk(abs_path):
            for file in files:
                filename, file_extension = os.path.splitext(file)
                # make copy of list of parsers
                good_parsers = self.parsers.copy()

                print("Checking:" + str(os.path.join(currentpath, file)))

                # start with file suffxies
                tmp_parsers = good_parsers.copy()
                print(file_extension)
                for parser in tmp_parsers:
                    print("Checking suffix:" + str(parser))
                    if not parser.can_accept_suffix(file_extension):
                        good_parsers.remove(parser)

                # now the filename
                tmp_parsers = good_parsers.copy()
                for parser in tmp_parsers:
                    print("Checking filename:" + str(parser))
                    if not parser.can_accept_filename(filename):
                        good_parsers.remove(parser)

                # now the first line
                tmp_parsers = good_parsers.copy()
                for parser in tmp_parsers:
                    print("Checking first_line:" + str(parser))
                    if not parser.can_accept_first_line(filename):
                        good_parsers.remove(parser)

                # get the file contents
                file_contents = "asdfas afgdg  d"

                # lastly the contents
                tmp_parsers = good_parsers.copy()
                for parser in tmp_parsers:
                    if not parser.can_process_file(file_contents):
                        good_parsers.remove(parser)

                # ok, let these parsers handle the file
                for parser in good_parsers:
                    print("Running:" + parser)
                    processed_ctr += 1
                    parser.process(data_store, file_contents)

        print("Files got processed:" + str(processed_ctr) + " times")

    def register(self, parser):
        """Add this parser
        
        :param parser: new parser
        :type parser: core_parser
        """
        self.parsers.append(parser)
