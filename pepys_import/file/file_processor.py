import os

from pepys_import.core.store.data_store import DataStore


class FileProcessor:
    def __init__(self, filename=None):
        self.importers = []
        if filename is None:
            self.filename = ":memory:"
        else:
            self.filename = filename

    def process(
        self, path: str, data_store: DataStore = None, descend_tree: bool = True
    ):
        """Process the data in the given path
        
        :param path: File/Folder path
        :type path: String
        :param data_store: Database
        :type data_store: DataStore
        :param descend_tree: Whether to recursively descend through the folder tree
        :type descend_tree: bool
        """

        processed_ctr = 0

        # check given path is a file
        if os.path.isfile(path):
            processed_ctr = self.process_file(path, path, data_store, processed_ctr)
            print(f"Files got processed: {processed_ctr} times")
            return

        # check folder exists
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Folder not found in the given path: {path}")

        # get the data_store, if necessary
        if data_store is None:
            data_store = DataStore("", "", "", 0, self.filename, db_type="sqlite")
            data_store.initialise()

        # capture path in absolute form
        abs_path = os.path.abspath(path)

        # decide whether to descend tree, or just work on this folder
        if descend_tree:
            # loop through this folder and children
            for current_path, folders, files in os.walk(abs_path):
                for file in files:
                    processed_ctr = self.process_file(
                        file, current_path, data_store, processed_ctr
                    )
        else:
            # loop through this path
            for file in os.scandir(abs_path):
                if file.is_file():
                    current_path = os.path.join(abs_path, file)
                    processed_ctr = self.process_file(
                        file, current_path, data_store, processed_ctr
                    )

        print(f"Files got processed: {processed_ctr} times")

    def process_file(self, file, current_path, data_store, processed_ctr):
        filename, file_extension = os.path.splitext(file)
        # make copy of list of importers
        good_importers = self.importers.copy()

        full_path = os.path.join(current_path, file)
        # print("Checking:" + str(full_path))

        # start with file suffixes
        tmp_importers = good_importers.copy()
        for importer in tmp_importers:
            # print("Checking suffix:" + str(importer))
            if not importer.can_load_this_type(file_extension):
                good_importers.remove(importer)

        # now the filename
        tmp_importers = good_importers.copy()
        for importer in tmp_importers:
            # print("Checking filename:" + str(importer))
            if not importer.can_load_this_filename(filename):
                good_importers.remove(importer)

        # tests are starting to get expensive. Check
        # we have some file importers left
        if len(good_importers) > 0:

            # now the first line
            tmp_importers = good_importers.copy()
            first_line = self.get_first_line(full_path)
            for importer in tmp_importers:
                # print("Checking first_line:" + str(importer))
                if not importer.can_load_this_header(first_line):
                    good_importers.remove(importer)

            # get the file contents
            file_contents = self.get_file_contents(full_path)

            # lastly the contents
            tmp_importers = good_importers.copy()
            for importer in tmp_importers:
                if not importer.can_load_this_file(file_contents):
                    good_importers.remove(importer)

            # ok, let these importers handle the file

            with data_store.session_scope():
                datafile = data_store.get_datafile(filename, file_extension)
                datafile_name = datafile.reference

            for importer in good_importers:
                processed_ctr += 1
                importer.load_this_file(data_store, file, file_contents, datafile_name)

        return processed_ctr

    def register_importer(self, importer):
        """Adds the supplied importer to the list of import modules
        
        :param importer: An importer module that must define the functions defined
        in the Importer base class
        :type importer: Importer
        """
        self.importers.append(importer)

    @staticmethod
    def get_first_line(file_path: str):
        """Retrieve the first line from the file

        :param file_path: Full file path
        :type file_path: String
        :return: First line of text
        :rtype: String
        """
        try:
            with open(file_path, "r", encoding="windows-1252") as f:
                first_line = f.readline()
            return first_line
        except UnicodeDecodeError:
            return None

    @staticmethod
    def get_file_contents(full_path: str):
        try:
            with open(full_path, "r", encoding="windows-1252") as f:
                lines = f.read().split("\n")
            return lines
        except UnicodeDecodeError:
            return None
