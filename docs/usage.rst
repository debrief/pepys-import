=====
Usage
=====

To use pepys-import in a project::

    from pepys_import.file.file_processor import FileProcessor
    from pepys_import.file.replay_parser import ReplayParser
    from pepys_import.file.nmea_parser import NMEAParser

    # create file processor, give it target filename
    processor = FileProcessor("trial_db.db")

    # register a couple of sample parsers
    processor.register(ReplayParser())
    processor.register(NMEAParser())

    # instruct Pepys to process this directory
    processor.process(".")
