=====
Usage
=====

To use pepys-import in a project::

    from pepys_import.file.file_processor import FileProcessor
    from pepys_import.file.replay_importer import ReplayImporter
    from pepys_import.file.nmea_importer import NMEAImporter

    # create file processor, give it target filename
    processor = FileProcessor("trial_db.db")

    # register a couple of sample parsers
    processor.register_importer(ReplayImporter())
    processor.register_importer(NMEAImporter())

    # instruct Pepys to process this directory
    processor.process(".")
