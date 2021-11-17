import os
from abc import ABC, abstractmethod

from tqdm import tqdm

from pepys_import.file.highlighter.level import HighlightLevel
from pepys_import.utils.text_formatting_utils import (
    custom_print_formatted_text,
    format_error_message,
)

CANCEL_IMPORT = "CANCEL"


class Importer(ABC):
    def __init__(self, name, validation_level, short_name, datafile_type, default_privacy=None):
        super().__init__()
        self.name = name
        self.validation_level = validation_level
        self.short_name = short_name
        self.default_privacy = default_privacy
        self.datafile_type = datafile_type
        self.errors = None
        self.error_type = None

        # By default all importers will record extractions to a highlighted
        # HTML file, but not record them to the database
        self.highlighting_level = HighlightLevel.HTML

    def __str__(self):
        return self.name

    def set_highlighting_level(self, level):
        """Sets the HighlightLevel of recording highlighted extractions. Can be one of:

        - NONE: No highlighting or recording of extractions
        - HTML: Produce a highlighted html file showing the extractions
        - DATABASE: Produce a highlighted html file and record extractions to the database"""
        self.highlighting_level = level

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

        datafile.current_measurement_object = None
        datafile.pending_extracted_tokens = []

        # Initialise the platform->sensor mapping here
        # so that we get a separate mapping for each file that we process
        self.platform_sensor_mapping = {}

        # Initialise the platform cache here
        # so we get a separate cache for each file we process
        self.platform_cache = {}

        file_object.importer_highlighting_levels[self.name] = self.highlighting_level

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
            result = self._load_this_line(data_store, line_number, line, datafile, change_id)
            if result == CANCEL_IMPORT:
                custom_print_formatted_text(
                    format_error_message(f"Error in file caused cancellation of import of {path}")
                )
                break

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

    def get_cached_sensor(self, data_store, sensor_name, sensor_type, platform_id, change_id):
        """Gets the sensor object for the given platform - either from the cache if it exists there,
        or resolving it.

        If the sensor_name and sensor_type are both None, and this platform_id is present in the
        self.platform_sensor_mapping dict, then get the Sensor object from there - otherwise use the
        resolver to resolve it.

        :param data_store: DataStore instance :type data_Store: DataStore :param platform_id: ID of
        the platform for which you want to get the sensor :type platform_id: int
        """
        Platform = data_store.db_classes.Platform

        if sensor_name is None and sensor_type is None:
            # Only look in the cache if the user hasn't specified any names or types
            sensor_from_cache = self.platform_sensor_mapping.get(platform_id)
            if sensor_from_cache is not None:
                return sensor_from_cache

            # Otherwise, resolve it
            platform_obj = (
                data_store.session.query(Platform)
                .filter(Platform.platform_id == platform_id)
                .first()
            )

            resolved_sensor = platform_obj.get_sensor(
                data_store=data_store,
                sensor_name=sensor_name,
                sensor_type=sensor_type,
                change_id=change_id,
            )

            data_store.session.expunge(resolved_sensor)
            # And store it in the cache for next time
            self.platform_sensor_mapping[platform_id] = resolved_sensor
        else:
            # sensor_name or sensor_type aren't None, so just resolve it and don't store in cache
            platform_obj = (
                data_store.session.query(Platform)
                .filter(Platform.platform_id == platform_id)
                .first()
            )

            resolved_sensor = platform_obj.get_sensor(
                data_store=data_store,
                sensor_name=sensor_name,
                sensor_type=sensor_type,
                change_id=change_id,
            )

        return resolved_sensor

    def get_cached_platform(
        self, data_store, platform_name, change_id, quadgraph=None, unknown=False
    ):
        if platform_name:
            # Look for this name in the cache first
            platform_from_cache = self.platform_cache.get(platform_name)
            if platform_from_cache is not None:
                return platform_from_cache

        # Otherwise use the resolver to find it
        resolved_platform = data_store.get_platform(
            platform_name=platform_name, quadgraph=quadgraph, change_id=change_id, unknown=unknown
        )

        # Put in the cache
        data_store.session.expunge(resolved_platform)
        # And store it in the cache for next time
        self.platform_cache[platform_name] = resolved_platform

        return resolved_platform
