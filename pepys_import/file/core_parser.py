from abc import ABC, abstractmethod


class CoreParser(ABC):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        return self.name

    @abstractmethod
    def can_accept_suffix(self, suffix) -> bool:
        """Whether this parser can handle a file with this suffix
        
        :param suffix: File suffix (e.g. ".doc")
        :type suffix: String
        :return: Yes/No
        :rtype: bool
        """
        pass

    @abstractmethod
    def can_accept_filename(self, filename) -> bool:
        """Whether this parser can handle a file with this full filename
        
        :param filename: Full filename
        :type filename: String
        :return: Yes/No
        :rtype: bool
        """
        pass

    @abstractmethod
    def can_accept_first_line(self, first_line) -> bool:
        """Whether this parser can handle a file with this initial line of text
        
        :param first_line: The initial line of text
        :type first_line: String
        :return: Yes/No
        :rtype: bool
        """
        pass

    @abstractmethod
    def can_process_file(self, file_contents) -> bool:
        """Whether this parser can handle this whole file
        
        :param file_contents: Whole file contents
        :type file_contents: String
        :return: Yes/No
        :rtype: bool
        """
        pass

    @abstractmethod
    def process(self, data_store, path, file_contents, data_file):
        """Process this data-file
        
        :param data_store: The data_store
        :type data_store: DataStore
        :param path: File File path
        :type path: String
        :param file_contents: File contents
        :type file_contents: String
        :param data_file: DataFile object
        :type data_file: DataFile
        """
        pass
