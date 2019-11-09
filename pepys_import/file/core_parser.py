from abc import ABC, abstractmethod


class core_parser(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def can_accept_suffix(self, suffix):
        pass

    @abstractmethod
    def can_accept_filename(self, filename):
        pass

    @abstractmethod
    def can_accept_first_line(self, first_line):
        pass

    @abstractmethod
    def can_process_file(self, file_contents):
        pass

    @abstractmethod
    def process(self, data_store, file_contents):
        pass
