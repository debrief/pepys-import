import inspect
import json
import os
import shutil
from datetime import datetime
from getpass import getuser
from stat import S_IREAD

from config import ARCHIVE_PATH, LOCAL_PARSERS
from paths import IMPORTERS_DIRECTORY
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.table_summary import TableSummary, TableSummarySet
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.importer import Importer
from pepys_import.file.smb_and_local_file_operations import (
    create_archive_path_if_not_exists,
    isdir,
    makedirs,
)
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
        self.archive = archive

        # Check if ARCHIVE_PATH is given in the config file
        if ARCHIVE_PATH:
            # Create the path if it doesn't exist
            create_archive_path_if_not_exists()
            self.output_path = ARCHIVE_PATH

    def process(self, path: str, data_store: DataStore = None, descend_tree: bool = True):
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

        # Create dict to store success/failures in
        import_summary = {}
        import_summary["succeeded"] = []
        import_summary["failed"] = []

        # Take current timestamp without milliseconds
        now = datetime.utcnow()
        # Create non existing directories in the following format:
        # output_folder/YYYY/MM/DD/HH/mm/ss(_sss)
        self.output_path = os.path.join(
            self.output_path,
            str(now.year),
            str(now.month).zfill(2),
            str(now.day).zfill(2),
            str(now.hour).zfill(2),
            str(now.minute).zfill(2),
            str(now.second).zfill(2),
        )
        if not isdir(self.output_path):
            makedirs(self.output_path)
        else:
            self.output_path = os.path.join(
                self.output_path + "_" + str(now.microsecond).zfill(3)[:3]
            )
            makedirs(self.output_path)

        # create input_files folder if not exists
        self.input_files_path = os.path.join(self.output_path, "sources")
        if not os.path.exists(self.input_files_path):
            os.makedirs(self.input_files_path)

        self.directory_path = os.path.join(self.output_path, "reports")
        if not os.path.isdir(self.directory_path):
            os.makedirs(self.directory_path)

        processed_ctr = 0

        # get the data_store
        if data_store is None:
            data_store = DataStore("", "", "", 0, self.filename, db_type="sqlite")
            data_store.initialise()

        # If given path is a single file, then just process that file
        if os.path.isfile(path):
            with data_store.session_scope():
                states_sum = TableSummary(data_store.session, data_store.db_classes.State)
                contacts_sum = TableSummary(data_store.session, data_store.db_classes.Contact)
                comments_sum = TableSummary(data_store.session, data_store.db_classes.Comment)
                platforms_sum = TableSummary(data_store.session, data_store.db_classes.Platform)
                first_table_summary_set = TableSummarySet(
                    [states_sum, contacts_sum, comments_sum, platforms_sum]
                )
                print(first_table_summary_set.report("==Before=="))

                filename = os.path.abspath(path)
                current_path = os.path.dirname(path)
                processed_ctr = self.process_file(
                    filename, current_path, data_store, processed_ctr, import_summary
                )
                states_sum = TableSummary(data_store.session, data_store.db_classes.State)
                contacts_sum = TableSummary(data_store.session, data_store.db_classes.Contact)
                comments_sum = TableSummary(data_store.session, data_store.db_classes.Comment)
                platforms_sum = TableSummary(data_store.session, data_store.db_classes.Platform)
                second_table_summary_set = TableSummarySet(
                    [states_sum, contacts_sum, comments_sum, platforms_sum]
                )
                print(second_table_summary_set.report("==After=="))
            self.display_import_summary(import_summary)
            print(f"Files got processed: {processed_ctr} times")
            return

        # If we've got to here then we're dealing with a folder

        # check folder exists
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Folder not found in the given path: {path}")

        # decide whether to descend tree, or just work on this folder
        with data_store.session_scope():

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            contacts_sum = TableSummary(data_store.session, data_store.db_classes.Contact)
            comments_sum = TableSummary(data_store.session, data_store.db_classes.Comment)
            platforms_sum = TableSummary(data_store.session, data_store.db_classes.Platform)
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
                            file, current_path, data_store, processed_ctr, import_summary
                        )
            else:
                # loop through this path
                for file in os.scandir(abs_path):
                    if file.is_file():
                        processed_ctr = self.process_file(
                            file, abs_path, data_store, processed_ctr, import_summary
                        )

            states_sum = TableSummary(data_store.session, data_store.db_classes.State)
            contacts_sum = TableSummary(data_store.session, data_store.db_classes.Contact)
            comments_sum = TableSummary(data_store.session, data_store.db_classes.Comment)
            platforms_sum = TableSummary(data_store.session, data_store.db_classes.Platform)
            second_table_summary_set = TableSummarySet(
                [states_sum, contacts_sum, comments_sum, platforms_sum]
            )
            print(second_table_summary_set.report("==After=="))

        self.display_import_summary(import_summary)
        print(f"Files got processed: {processed_ctr} times")

    def process_file(self, file_object, current_path, data_store, processed_ctr, import_summary):
        # file may have full path, therefore extract basename and split it
        basename = os.path.basename(file_object)
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
            change = data_store.add_to_changes(user=USER, modified=datetime.utcnow(), reason=reason)
            privacy = None
            for importer in good_importers:
                if importer.default_privacy:
                    privacy = importer.default_privacy
                    break
            datafile = data_store.get_datafile(
                basename, file_extension, file_size, file_hash, change.change_id, privacy=privacy,
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
            importers_with_errors = []
            validators_with_errors = []

            for importer in good_importers:
                # If the importer has errors then note this, so we can inform the user
                if len(importer.errors) > 0:
                    importers_with_errors.append(importer.short_name)

                # Call related validation tests, extend global errors lists if the
                # importer has errors
                validation_errors = []
                validated, failed_validators = datafile.validate(
                    validation_level=importer.validation_level,
                    errors=validation_errors,
                    parser=importer.short_name,
                )
                # Add the list of failed validators from that importer to
                # the overall list of validators with errors for this file
                validators_with_errors.extend(failed_validators)

                # Add the importer errors and the validation errors to the list
                # of errors for this file
                errors.extend(importer.errors)
                errors.extend(validation_errors)

            # If all tests pass for all parsers, commit datafile
            if not errors:
                log = datafile.commit(data_store, change.change_id)

                # Keep track of some details for the import summary
                summary_details = {}
                summary_details["filename"] = basename

                # write extraction log to output folder
                with open(
                    os.path.join(self.directory_path, f"{filename}_output.log"), "w",
                ) as file:
                    file.write("\n".join(log))
                if self.archive is True:
                    # move original file to output folder
                    new_path = os.path.join(self.input_files_path, basename)
                    shutil.move(full_path, new_path)
                    # make it read-only
                    os.chmod(new_path, S_IREAD)
                    summary_details["archived_location"] = new_path
                import_summary["succeeded"].append(summary_details)

            else:
                failure_report_filename = os.path.join(
                    self.directory_path, f"{filename}_errors.log"
                )
                # write error log to the output folder
                with open(failure_report_filename, "w") as file:
                    json.dump(errors, file, ensure_ascii=False, indent=4)
                import_summary["failed"].append(
                    {
                        "filename": basename,
                        "importers_with_errors": importers_with_errors,
                        "validators_with_errors": validators_with_errors,
                        "report_location": failure_report_filename,
                    }
                )

        return processed_ctr

    def display_import_summary(self, import_summary):
        if len(import_summary["succeeded"]) > 0:
            print("Import succeeded for:")
            for details in import_summary["succeeded"]:
                if "archived_location" in details:
                    print(f"  - {details['filename']}")
                    print(f"    - Archived to {details['archived_location']}")
                else:
                    print(f"  - {details['filename']}")
            print()
        if len(import_summary["failed"]) > 0:
            print("Import failed for:")
            for details in import_summary["failed"]:
                failed_importers_list = "\n".join(
                    [f"      - {name}" for name in details["importers_with_errors"]]
                )
                failed_validators_list = "\n".join(
                    [f"      - {name}" for name in set(details["validators_with_errors"])]
                )
                print(f"  - {details['filename']}")
                if len(failed_importers_list) > 0:
                    print("    - Importers failing:")
                    print(failed_importers_list)
                if len(failed_validators_list) > 0:
                    print("    - Validators failing:")
                    print(failed_validators_list)
                print(f"    - Failure report at {details['report_location']}")
            print()

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
                        if issubclass(class_, Importer) and not inspect.isabstract(class_):
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
            with open(file_path, "r", encoding="windows-1252") as file:
                first_line = file.readline()
            return first_line
        except UnicodeDecodeError:
            return None

    @staticmethod
    def get_file_contents(full_path: str):
        try:
            with open(full_path, "r", encoding="windows-1252") as file:
                lines = file.read().split("\n")
            return lines
        except UnicodeDecodeError:
            return None
