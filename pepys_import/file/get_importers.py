from pepys_import.file.replay_importer import ReplayImporter
from pepys_import.file.replay_comment_importer import ReplayCommentImporter
from pepys_import.file.nmea_importer import NMEAImporter
from pepys_import.file.gpx_importer import GPXImporter
from pepys_import.file.e_trac_importer import ETracImporter


def get_importers():
    """
    Returns a list of importers to be added to the file_processor object.

    At the moment this just returns the static list of importers that we include
    with pepys-import. Later, this will dynamically find importers in various places
    and add them to the list
    """

    STATIC_IMPORTERS = [
        ReplayImporter(),
        ReplayCommentImporter(),
        NMEAImporter(),
        GPXImporter(),
        ETracImporter(),
    ]

    return STATIC_IMPORTERS
