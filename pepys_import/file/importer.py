from abc import ABC, abstractmethod


class Importer(ABC):
    name = "Importer"

    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.name

    @abstractmethod
    def can_load_this_type(self, suffix) -> bool:
        """Whether this importer can load files with the specified suffix.
        
        :param suffix: File suffix (e.g. ".doc")
        :type suffix: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_filename(self, filename) -> bool:
        """Whether this importer can load a file with the provided filename
        
        :param filename: Full filename
        :type filename: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_header(self, header) -> bool:
        """Whether this importer can load a file with this first line of text
        
        :param header: The initial line of text
        :type header: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def can_load_this_file(self, file_contents) -> bool:
        """Whether this parser can handle this whole file
        
        :param file_contents: Whole file contents
        :type file_contents: String
        :return: Yes/No
        :rtype: bool
        """

    @abstractmethod
    def load_this_file(self, data_store, path, file_contents, datafile):
        """Process this data-file
        
        :param data_store: The data_store
        :type data_store: DataStore
        :param path: File File path
        :type path: String
        :param file_contents: File contents
        :type file_contents: String
        :param datafile: DataFile object
        :type datafile: DataFile
        """
