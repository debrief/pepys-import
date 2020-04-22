import os
from abc import ABC, abstractmethod

from tqdm import tqdm


class Importer(ABC):
    def __init__(self, name, validation_level, short_name, default_privacy=None):
        super().__init__()
        self.name = name
        self.validation_level = validation_level
        self.short_name = short_name
        self.default_privacy = default_privacy
        self.errors = None
        self.error_type = None

        self.do_recording = True

    def __str__(self):
        return self.name

    def disable_recording(self):
        self.do_recording = False

    @abstractmethod
    def can_load_this_type(self, suffix) -> bool:
        """Whether this importer can load files with the specified suffix.

        :param suffix: File suffix (e.g. ".doc")
        :type suffix: String
        :return: True/False
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_filename(self, filename) -> bool:
        """Whether this importer can load a file with the provided filename

        :param filename: Full filename
        :type filename: String
        :return: True/False
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_header(self, header) -> bool:
        """Whether this importer can load a file with this first line of text

        :param header: The initial line of text
        :type header: String
        :return: True/False
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_file(self, file_contents) -> bool:
        """Whether this parser can handle this whole file

        :param file_contents: Whole file contents
        :type file_contents: String
        :return: True/False
        :rtype: bool
        """

    def load_this_file(self, data_store, path, file_object, datafile, change_id):
        """Loads the specified file.

        Performs the common administrative operations that must be performed
        before the _load_this_file method is called, then calls that function.

        :param data_store: The DataStore object connected to the database into which the
                           file should be loaded
        :type data_store: DataStore
        :param path: The full path to the file to import
        :type path: String
        :param file_object: The HighlightedFile object representing the file, allowing
                            access to lines and tokens
        :type file_object: HighlightedFile
        :param datafile: The Datafile object referring to the file to be imported
        :type datafile: Datafile
        :param change_id: ID of the :class:`Change` object that represents the change
                          which will occur when importing this file
        :type change_id: Integer or UUID

        """
        basename = os.path.basename(path)
        print(f"{self.short_name} working on {basename}")
        self.errors = list()
        self.error_type = f"{self.short_name} - Parsing error on {basename}"
        datafile.measurements[self.short_name] = dict()

        # If we've turned off recording of extractions for this importer
        # then add this to the list of ignored importers for this HighlightedFile
        # object
        if not self.do_recording:
            file_object.ignored_importers.append(self.name)

        # perform load
        self._load_this_file(data_store, path, file_object, datafile, change_id)

    def _load_this_file(self, data_store, path, file_object, datafile, change_id):
        """Process this data-file

        :param data_store: The DataStore object connected to the database into which the
        file should be loaded
        :type data_store: DataStore
        :param path: The full path to the file to import
        :type path: String
        :param file_object: The HighlightedFile object representing the file, allowing
        access to lines and tokens
        :type file_object: HighlightedFile
        :param datafile: The Datafile object referring to the file to be imported
        :type datafile: Datafile
        :param change_id: ID of the :class:`Change` object that represents the change
        which will occur when importing this file
        :type change_id: integer or UUID
        """
        for line_number, line in enumerate(tqdm(file_object.lines()), 1):
            self._load_this_line(data_store, line_number, line, datafile, change_id)

    def _load_this_line(self, data_store, line_number, line, datafile, change_id):
        """Process a line from this data-file

        :param data_store: The data_store
        :type data_store: DataStore
        :param line_number: The number of the line in the file (starting from 1)
        :type line_number: Integer
        :param line: A Line object, representing a line from a file and allowing
        extraction of tokens, and recording of tokens
        :type line: :class:`Line`
        :param datafile: DataFile object
        :type datafile: DataFile
        :param change_id: ID of the :class:`Change` object that represents the change
        which will occur when importing this line
        :type change_id: integer or UUID
        """
        raise NotImplementedError
