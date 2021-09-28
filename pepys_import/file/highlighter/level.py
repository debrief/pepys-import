from enum import Enum


class HighlightLevel(Enum):
    """The level of recording highlighted extractions"""

    NONE = 1
    """No highlighting or recording of extractions"""
    HTML = 2
    """Produce a highlighted HTML file showing the extractions"""
    DATABASE = 3
    """Produce a highlighted HTML file and record extractions to the database"""
