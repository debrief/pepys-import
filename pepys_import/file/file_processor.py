import inspect
import importlib.util
import json
import os
import shutil
import sys

from datetime import datetime
from getpass import getuser
from stat import S_IREAD

from paths import IMPORTERS_DIRECTORY
from config import ARCHIVE_PATH, LOCAL_PARSERS
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary, TableSummarySet
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.importer import Importer
from pepys_import.utils.datafile_utils import hash_file
from pepys_import.utils.import_utils import import_module_

USER = getuser()


class FileProcessor:
    def __init__(self, filename=None, archive=False):
        self.importers = []
        # Register local importers if any exists
        if LOCAL_PARSERS:
            if not os.path.exists(LOCAL_PARSERS):
                print(
                    f"No such file or directory: {LOCAL_PARSERS}. Only core "
                    "parsers are going to work."
                )
            else:
                self.load_importers_dynamically(LOCAL_PARSERS)

        if filename is None:
            self.filename = ":memory:"
        else:
            self.filename = filename
        self.output_path = None
        self.input_files_path = None
        self.directory_path = None
        # Check if ARCHIVE_PATH is given in the config file
        if ARCHIVE_PATH:
            # Create the path if it doesn't exist
            if not os.path.exists(ARCHIVE_PATH):
                os.makedirs(ARCHIVE_PATH)
            self.output_path = ARCHIVE_PATH
        self.archive = archive

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
        dir_path = os.path.dirname(path)
        # create output folder if not exists
        if not self.output_path:
            self.output_path = os.path.join(dir_path, "output")
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
        # create input_files folder if not exists
        self.input_files_path = os.path.join(self.output_path, "input_files")
        if not os.path.exists(self.input_files_path):
            os.makedirs(self.input_files_path)

        # Take current timestamp without milliseconds
        now = datetime.utcnow()
        # Create non existing directories in the following format:
        # output_folder/YYYY/MM/DD/HH/mm/ss(_sss)
        directory_path = os.path.join(
            self.output_path,
            str(now.year),
            str(now.month).zfill(2),
            str(now.day).zfill(2),
            str(now.hour).zfill(2),
            str(now.minute).zfill(2),
            str(now.second).zfill(2),
        )
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)
        else:
            directory_path = os.path.join(
                directory_path + "_" + str(now.microsecond).zfill(3)[:3]
            )
            os.makedirs(directory_path)
        self.directory_path = directory_path

        processed_ctr = 0

        # get the data_store
        if data_store is None:
            data_store = DataStore("", "", "", 0, self.filename, db_type="sqlite")
            data_store.initialise()

        # check given path is a file
        if os.path.isfile(path):
            with data_store.session_scope():
                states_sum = TableSummary(
                    data_store.session, data_store.db_classes.State
                )
                contacts_sum = TableSummary(
                    data_store.session, data_store.db_classes.Contact
                )
                comments_sum = TableSummary(
                    data_store.session, data_store.db_classes.Comment
                )
                platforms_sum = TableSummary(
                    data_store.session, data_store.db_classes.Platform
                )
                first_table_summary_set = TableSummarySet(
                    [states_sum, contacts_sum, comments_sum, platforms_sum]
                )
                print(first_table_summary_set.report("==Before=="))

                filename = os.path.abspath(path)
                current_path = os.path.dirname(path)
                processed_ctr = self.process_file(
                    filename, current_path, data_store, processed_ctr
                )
                states_sum = TableSummary(
                    data_store.session, data_store.db_classes.State
                )
                contacts_sum = TableSummary(
                    data_store.session, data_store.db_classes.Contact
                )
                comments_sum = TableSummary(
                    data_store.session, data_store.db_classes.Comment
                )
                platforms_sum = TableSummary(
                    data_store.session, data_store.db_classes.Platform
                )
                second_table_summary_set = TableSummarySet(
                    [states_sum, contacts_sum, comments_sum, platforms_sum]
                )
                print(second_table_summary_set.report("==After=="))
            print(f"Files got processed: {processed_ctr} times")
            return

        # check folder exists
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Folder not found in the given path: {path}")

        # decide whether to descend tree, or just work on this folder
        with data_store.session_scope():

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            contacts_sum = TableSummary(
                data_store.session, data_store.db_classes.Contact
            )
            comments_sum = TableSummary(
                data_store.session, data_store.db_classes.Comment
            )
            platforms_sum = TableSummary(
                data_store.session, data_store.db_classes.Platform
            )
            first_table_summary_set = TableSummarySet(
                [states_sum, contacts_sum, comments_sum, platforms_sum]
            )
            print(first_table_summary_set.report("==Before=="))

            # capture path in absolute form
            abs_path = os.path.abspath(path)
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
                        processed_ctr = self.process_file(
                            file, abs_path, data_store, processed_ctr
                        )

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            contacts_sum = TableSummary(
                data_store.session, data_store.db_classes.Contact
            )
            comments_sum = TableSummary(
                data_store.session, data_store.db_classes.Comment
            )
            platforms_sum = TableSummary(
                data_store.session, data_store.db_classes.Platform
            )
            second_table_summary_set = TableSummarySet(
                [states_sum, contacts_sum, comments_sum, platforms_sum]
            )
            print(second_table_summary_set.report("==After=="))

        print(f"Files got processed: {processed_ctr} times")

    def process_file(self, file, current_path, data_store, processed_ctr):
        # file may have full path, therefore extract basename and split it
        basename = os.path.basename(file)
        filename, file_extension = os.path.splitext(basename)
        # make copy of list of importers
        good_importers = self.importers.copy()

        full_path = os.path.join(current_path, basename)
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

            # Create a HighlightedFile instance for the file
            highlighted_file = HighlightedFile(full_path)

            # Get the file contents, for the final check
            file_contents = self.get_file_contents(full_path)

            # lastly the contents
            tmp_importers = good_importers.copy()
            for importer in tmp_importers:
                if not importer.can_load_this_file(file_contents):
                    good_importers.remove(importer)

            # if good importers list is empty, return processed_ctr,
            # which means the file is not processed
            if not good_importers:
                return processed_ctr

            # If the file is loaded before, return processed_ctr,
            # which means the file is not processed again
            file_size = os.path.getsize(full_path)
            file_hash = hash_file(full_path)
            if data_store.is_datafile_loaded_before(file_size, file_hash):
                return processed_ctr

            # ok, let these importers handle the file
            reason = f"Importing '{basename}'."
            change = data_store.add_to_changes(
                user=USER, modified=datetime.utcnow(), reason=reason
            )
            datafile = data_store.get_datafile(
                basename, file_extension, file_size, file_hash, change.change_id
            )

            # Run all parsers
            for importer in good_importers:
                processed_ctr += 1
                importer.load_this_file(
                    data_store, full_path, highlighted_file, datafile, change.change_id
                )

            # Write highlighted output to file
            highlighted_output_path = os.path.join(
                self.directory_path, f"{filename}_highlighted.html"
            )

            highlighted_file.export(highlighted_output_path, include_key=True)

            # Run all validation tests
            errors = list()
            for importer in good_importers:
                # Call related validation tests, extend global errors lists if the
                # importer has errors
                if not datafile.validate(
                    validation_level=importer.validation_level,
                    errors=importer.errors,
                    parser=importer.short_name,
                ):
                    errors.extend(importer.errors)

            # If all tests pass for all parsers, commit datafile
            if not errors:
                log = datafile.commit(data_store, change.change_id)
                # write extraction log to output folder
                with open(
                    os.path.join(self.directory_path, f"{filename}_output.log"), "w",
                ) as f:
                    f.write("\n".join(log))
                if self.archive is True:
                    # move original file to output folder
                    new_path = os.path.join(self.input_files_path, basename)
                    shutil.move(full_path, new_path)
                    # make it read-only
                    os.chmod(new_path, S_IREAD)
            else:
                # write error log to the output folder
                with open(
                    os.path.join(self.directory_path, f"{filename}_errors.log"), "w",
                ) as f:
                    json.dump(errors, f, ensure_ascii=False, indent=4)

        return processed_ctr

    def register_importer(self, importer):
        """Adds the supplied importer to the list of import modules

        :param importer: An importer module that must define the functions defined
        in the Importer base class
        :type importer: Importer
        
        """
        self.importers.append(importer)

    def load_importers_dynamically(self, path=IMPORTERS_DIRECTORY):
        """Dynamically adds all the importers in the given path.

        It loads core importers by default.

        :param path: Path of a folder that has importers
        :type path: String
        """
        if os.path.exists(path):
            for file in os.scandir(path):
                # import file using its name and full path
                if file.is_file():
                    classes = import_module_(file)
                    for name, class_ in classes:
                        # continue only if it's a concrete class that inherits Importer
                        if issubclass(class_, Importer) and not inspect.isabstract(
                            class_
                        ):
                            # Create an object of the class, add it to importers
                            obj = class_()
                            self.importers.append(obj)

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
