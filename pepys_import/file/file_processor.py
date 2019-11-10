import os

from pepys_import.core.store.data_store import DataStore


class file_processor:
    def __init__(self):
        self.parsers = []

    def process(self, folder: str, data_store: DataStore, descend_tree: bool = True):
        """Process this folder of data
        
        :param folder: Folder path
        :type folder: String
        :param data_Store: Database
        :type data_store: DataStore
        :param descend_tree: Whether to recursively descend through the folder tree
        :type descend_tree: bool
        """

        processed_ctr = 0

        # check folder exists
        if not os.path.isdir(folder):
            raise Exception("Folder not found: {}".format(folder))

        # get the datastore
        data_store = DataStore("", "", "", 0, "bulk_load.db", db_type="sqlite")
        data_store.initialise()

        # make copy of list of parsers
        good_parsers = self.parsers.copy()

        filename, file_extension = os.path.splitext(folder)

        # capture path in absolute form
        abs_path = os.path.abspath(folder)

        # decide whether to descend tree, or just work on this folder
        if descend_tree:
            # loop through this folder and children
            for currentpath, folders, files in os.walk(abs_path):
                for file in files:
                    processed_ctr = self.processFile(
                        file, currentpath, good_parsers, data_store, processed_ctr
                    )
        else:
            # loop through this folder
            for file in os.scandir(abs_path):
                if file.is_file():
                    currentpath = os.path.join(abs_path, file)
                    processed_ctr = self.processFile(
                        file, currentpath, good_parsers, data_store, processed_ctr
                    )

        print("Files got processed:" + str(processed_ctr) + " times")

    def get_first_line(self, path):
        """Retrieve the first line from the file
        
        :param path: Full tile path
        :type path: String
        :return: First line of text
        :rtype: String
        """
        try:
            with open(path, "r", encoding="windows-1252") as f:
                first_line = f.readline()
                return first_line
        except UnicodeDecodeError:
            return None
        finally:
            f.close()

    def get_file_contents(self, full_path: str):
        try:
            with open(full_path, "r", encoding="windows-1252") as f:
                lines = f.read().split("\n")
        finally:
            f.close()
        return lines

    def processFile(self, file, currentpath, good_parsers, data_store, processed_ctr):
        filename, file_extension = os.path.splitext(file)
        # make copy of list of parsers
        good_parsers = self.parsers.copy()

        full_path = os.path.join(currentpath, file)
        # print("Checking:" + str(full_path))

        # start with file suffxies
        tmp_parsers = good_parsers.copy()
        for parser in tmp_parsers:
            # print("Checking suffix:" + str(parser))
            if not parser.can_accept_suffix(file_extension):
                good_parsers.remove(parser)

        # now the filename
        tmp_parsers = good_parsers.copy()
        for parser in tmp_parsers:
            # print("Checking filename:" + str(parser))
            if not parser.can_accept_filename(filename):
                good_parsers.remove(parser)

        # tests are starting to get expensive. Check
        # we have some file parsers left
        if len(good_parsers) > 0:

            # now the first line
            tmp_parsers = good_parsers.copy()
            first_line = self.get_first_line(full_path)
            for parser in tmp_parsers:
                # print("Checking first_line:" + str(parser))
                if not parser.can_accept_first_line(first_line):
                    good_parsers.remove(parser)

            # get the file contents
            file_contents = self.get_file_contents(full_path)

            # lastly the contents
            tmp_parsers = good_parsers.copy()
            for parser in tmp_parsers:
                if not parser.can_process_file(file_contents):
                    good_parsers.remove(parser)

            # ok, let these parsers handle the file

            with data_store.session_scope() as session:
                data_file = session.add_to_datafile_from_rep(filename, file_extension)
                data_file_id = data_file.datafile_id
                session.close()

            for parser in good_parsers:
                processed_ctr += 1
                parser.process(data_store, file, file_contents, data_file_id)

        return processed_ctr

    def register(self, parser):
        """Add this parser
        
        :param parser: new parser
        :type parser: core_parser
        """
        self.parsers.append(parser)
