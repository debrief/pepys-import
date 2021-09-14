import inspect
import json
import os
import shutil
from datetime import datetime
from getpass import getuser
from stat import S_IREAD

from halo import Halo
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator

from paths import IMPORTERS_DIRECTORY
from pepys_import import __build_timestamp__, __version__
from pepys_import.core.store import constants
from pepys_import.core.store.data_store import DataStore
from pepys_import.core.store.db_status import TableTypes
from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.importer import Importer
from pepys_import.resolvers.command_line_resolver import CommandLineResolver
from pepys_import.utils.datafile_utils import hash_file
from pepys_import.utils.import_utils import import_module_, sort_files
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.table_name_utils import table_name_to_class_name
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
    format_table,
    print_new_section_title,
)

USER = getuser()


class FileProcessor:
    def __init__(
        self,
        filename=None,
        archive=False,
        skip_validation=False,
        archive_path=None,
        local_parsers=None,
    ):
        self.importers = []
        # Register local importers if any exists
        if local_parsers:
            if not os.path.exists(local_parsers):
                custom_print_formatted_text(
                    format_error_message(
                        f"No such file or directory: {local_parsers}. Only core "
                        "parsers are going to work."
                    )
                )
            else:
                self.load_importers_dynamically(local_parsers)

        if filename is None:
            self.filename = ":memory:"
        else:
            self.filename = filename
        self.output_path = None
        self.input_files_path = None
        self.directory_path = None

        self.archive = archive

        if self.archive:
            # Only create the archive folder if we are actually going
            # to be doing archiving
            if archive_path:
                # Create the path if it doesn't exist
                try:
                    if not os.path.exists(archive_path):
                        os.makedirs(archive_path)
                    self.output_path = archive_path
                except Exception as e:
                    raise ValueError(
                        f"Could not create archive folder at {archive_path}. Original error: {str(e)}"
                    )

        self.skip_validation = skip_validation

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

        # Create dict to store success/failures/skipped in
        import_summary = {}
        import_summary["succeeded"] = []
        import_summary["failed"] = []
        import_summary["skipped"] = []

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
        if not os.path.isdir(self.output_path):
            os.makedirs(self.output_path)
        else:
            self.output_path = os.path.join(
                self.output_path + "_" + str(now.microsecond).zfill(3)[:3]
            )
            os.makedirs(self.output_path)

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
                filename = os.path.abspath(path)
                current_path = os.path.dirname(path)

                processed_ctr = self.process_file(
                    filename,
                    current_path,
                    data_store,
                    processed_ctr,
                    import_summary,
                    file_number=1,
                    total_files=1,
                )
            self.display_import_summary(import_summary)
            print(f"Files got processed: {processed_ctr} times")
            abs_path = os.path.abspath(self.output_path)
            print(f"Archive/report folders can be found at {abs_path}")
            return

        # If we've got to here then we're dealing with a folder

        # check folder exists
        if not os.path.isdir(path):
            raise FileNotFoundError(f"Folder not found in the given path: {path}")

        # decide whether to descend tree, or just work on this folder
        with data_store.session_scope():
            # capture path in absolute form
            abs_path = os.path.abspath(path)
            if descend_tree:
                # loop through this folder and children and store in list
                # (so we know how many we have)
                files_and_paths = []
                for current_path, folders, files in os.walk(abs_path):
                    for file in sort_files(files):
                        files_and_paths.append((file, current_path))

                for i, (file, current_path) in enumerate(files_and_paths, start=1):
                    processed_ctr = self.process_file(
                        file,
                        current_path,
                        data_store,
                        processed_ctr,
                        import_summary,
                        file_number=i,
                        total_files=len(files_and_paths),
                    )
            else:
                # loop through this path
                files_in_folder = [
                    file for file in sort_files(os.scandir(abs_path)) if file.is_file()
                ]

                for i, file in enumerate(files_in_folder, start=1):
                    processed_ctr = self.process_file(
                        file,
                        abs_path,
                        data_store,
                        processed_ctr,
                        import_summary,
                        file_number=i,
                        total_files=len(files_in_folder),
                    )

        self.display_import_summary(import_summary)
        print(f"Files got processed: {processed_ctr} times")

    def process_file(
        self,
        file_object,
        current_path,
        data_store,
        processed_ctr,
        import_summary,
        file_number,
        total_files,
    ):
        # file may have full path, therefore extract basename and split it
        basename = os.path.basename(file_object)
        filename, file_extension = os.path.splitext(basename)

        if basename == ".DS_Store":
            return processed_ctr

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
            try:
                file_contents = self.get_file_contents(full_path)
            except Exception:
                # Can't get the file contents - eg. because it's not a proper
                # unicode text file (This can occur for binary files in the same folders)
                # So skip the file
                return processed_ctr

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

            reason = f"Importing '{basename}' using Pepys {__version__}"
            # ok, let these importers handle the file
            if __build_timestamp__ is not None:
                reason += f", built on {__build_timestamp__}"

            change = data_store.add_to_changes(user=USER, modified=datetime.utcnow(), reason=reason)
            privacy = None
            for importer in good_importers:
                if importer.default_privacy:
                    privacy = importer.default_privacy
                    break

            exclude = [
                constants.CHANGE,
                constants.DATAFILE,
                constants.EXTRACTION,
                constants.LOG,
            ]

            metadata_summaries_before = data_store.get_status(TableTypes.METADATA, exclude=exclude)
            measurement_summaries_before = data_store.get_status(
                TableTypes.MEASUREMENT, exclude=exclude
            )

            # This will produce a header with a progress counter
            # Be aware that the denominator is the count of all files in the path to be imported
            # and Pepys may ignore some (or many) of these files if they aren't types that Pepys recognises
            # So it could say "Importing file 1 of 500" and then only import 3 files, if the other 497 are
            # files that no Pepys importers recognise
            print_new_section_title(f"Processing file {file_number} of {total_files}:\n{basename}")

            # We assume that good importers will have the same datafile-type values at the moment.
            # That's why we can create a datafile using the first importer's datafile_type.
            # They don't have different datafile-type values, but if necessary, we might iterate over
            # good importers and find a composite datafile-type.
            datafile = data_store.get_datafile(
                basename,
                good_importers[0].datafile_type,
                file_size,
                file_hash,
                change.change_id,
                privacy=privacy,
            )

            # Update change object
            change.datafile_id = datafile.datafile_id
            data_store.session.flush()

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

            print(f"Writing highlighted file for {basename}")
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
                    skip_validation=self.skip_validation,
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
                # Keep track of some details for the import summary
                summary_details = {}
                summary_details["filename"] = basename

                log = datafile.commit(data_store, change.change_id)
                metadata_summaries_after = data_store.get_status(
                    TableTypes.METADATA, exclude=exclude
                )
                measurement_summaries_after = data_store.get_status(
                    TableTypes.MEASUREMENT, exclude=exclude
                )
                metadata_report = metadata_summaries_after.show_delta_of_rows_added_metadata(
                    metadata_summaries_before
                )
                formatted_text = format_table("METADATA REPORT", table_string=metadata_report)
                custom_print_formatted_text(formatted_text)

                measurement_report = measurement_summaries_after.show_delta_of_rows_added(
                    measurement_summaries_before
                )
                formatted_text = format_table("MEASUREMENT REPORT", table_string=measurement_report)
                custom_print_formatted_text(formatted_text)
                if isinstance(data_store.missing_data_resolver, CommandLineResolver):
                    choices = (
                        "Import metadata",
                        "Import metadata and measurements",
                        "Don't import data from this file.",
                    )
                    choice = self._ask_user_for_finalizing_import(choices)
                else:  # default is Import metadata and measurements
                    choice = "2"

                if choice == "1":  # Import metadata
                    self._remove_measurements(data_store, datafile, change.change_id)
                    data_store.session.commit()
                    # Set log to an empty list because measurements are deleted
                    log = []
                elif choice == "2":  # Import metadata and measurements
                    pass
                else:  # Don't import data from this file.
                    # Remove metadata and measurement
                    self._remove_measurement_and_metadata(data_store, datafile, change.change_id)
                    data_store.session.commit()
                    import_summary["skipped"].append(summary_details)
                    return processed_ctr

                # write extraction log to output folder
                with open(
                    os.path.join(self.directory_path, f"{filename}_output.log"),
                    "w",
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
                metadata_summaries_after = data_store.get_status(
                    TableTypes.METADATA, exclude=exclude
                )
                metadata_report = metadata_summaries_after.show_delta_of_rows_added_metadata(
                    metadata_summaries_before
                )
                formatted_text = format_table("METADATA REPORT", table_string=metadata_report)
                custom_print_formatted_text(formatted_text)
                if isinstance(data_store.missing_data_resolver, CommandLineResolver):
                    choices = (
                        "Import metadata",
                        "Don't import data from this file.",
                    )
                    choice = self._ask_user_for_finalizing_import(choices)
                else:  # Default is import metadata
                    choice = "1"

                if choice == "1":  # Import metadata
                    self._remove_measurements(data_store, datafile, change.change_id)
                elif choice == "2":  # Don't import data from this file
                    self._remove_measurement_and_metadata(data_store, datafile, change.change_id)
                data_store.session.commit()

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

    def _remove_measurement_and_metadata(self, data_store, datafile, change_id):
        # Remove measurement entities
        self._remove_measurements(data_store, datafile, change_id)
        # Remove metadata entities
        self._remove_metadata(data_store, change_id)

    @staticmethod
    def _remove_measurements(data_store, datafile, change_id):
        # Delete the datafile entry, as we won't be importing any entries linked to it,
        # because we had errors. CASCADING will handle the deletion of the all measurement objects
        # of the datafile
        spinner = Halo(text="@ Clearing measurements", spinner="dots")
        spinner.start()
        data_store.session.delete(datafile)
        # Remove log objects
        objects_from_logs = data_store.get_logs_by_change_id(change_id)
        for obj in objects_from_logs:
            table_cls = getattr(data_store.db_classes, table_name_to_class_name(obj.table))
            if table_cls.table_type == TableTypes.MEASUREMENT:
                data_store.session.delete(obj)
        spinner.succeed("Measurements cleared")

    @staticmethod
    def _remove_metadata(data_store, change_id):
        spinner = Halo(text="@ Clearing metadata", spinner="dots")
        spinner.start()
        objects_from_logs = data_store.get_logs_by_change_id(change_id)
        for obj in objects_from_logs:
            table_cls = getattr(data_store.db_classes, table_name_to_class_name(obj.table))
            if table_cls.table_type == TableTypes.METADATA:
                primary_key_field = getattr(table_cls, get_primary_key_for_table(table_cls))
                data_store.session.query(table_cls).filter(primary_key_field == obj.id).delete()
                # Remove Logs entity
                data_store.session.delete(obj)
        spinner.succeed("Metadata cleared")

    @staticmethod
    def display_import_summary(import_summary):
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
        if len(import_summary["skipped"]) > 0:
            print("Import skipped for:")
            for details in import_summary["skipped"]:
                print(f"  - {details['filename']}")

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
            for file in sort_files(os.scandir(path)):
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
        with open(full_path, "r", encoding="windows-1252") as file:
            lines = file.read().split("\n")
        return lines

    @staticmethod
    def _input_validator(options):
        def is_valid(option):
            return option in [str(o) for o, _ in enumerate(options, 1)]

        validator = Validator.from_callable(
            is_valid,
            error_message="You didn't select a valid option",
            move_cursor_to_end=True,
        )
        return validator

    def _ask_user_for_finalizing_import(self, choices):
        validator = self._input_validator(choices)
        input_text = "\n\nWould you like to\n"
        for index, choice in enumerate(choices, 1):
            input_text += f"   {str(index)}) {choice}\n"
        choice = prompt(input_text, validator=validator)
        return choice
