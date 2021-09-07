import os
import re

import pexpect


def test_gpx_import_end_to_end():
    if os.path.exists("pexpect_test.db"):
        os.remove("pexpect_test.db")

    child = pexpect.spawn(
        "python -m pepys_import.cli --path tests/sample_data/track_files/gpx/gpx_1_0.gpx --db pexpect_test.db",
        encoding="utf-8",
    )

    child.logfile = open("pexpect.log", "w")

    # Classification for datafile: Public
    child.expect_exact("> ")
    child.sendline("2")

    # Create datafile: Yes
    child.expect_exact("> ")
    child.sendline("1")

    # Select platform: Add new platform
    child.expect_exact("> ")
    child.sendline("1")

    # Enter a name: (accept default)
    child.expect_exact("NELSON")
    child.sendline("")

    # Enter pennant or tail number: 123
    child.expect_exact("pennant or tail number")
    child.sendline("123")

    # Enter trigraph: (accept default)
    child.expect_exact("trigraph (optional)")
    child.sendline("")

    # Enter quadgraph: (accept default)
    child.expect_exact("quadgraph")
    child.sendline("")

    # Select nationality: UK
    child.expect_exact("> ")
    child.sendline("2")

    # Select platform type: Naval - frigate
    child.expect_exact("> ")
    child.sendline("3")

    # Select classification: Public
    child.expect_exact("> ")
    child.sendline("2")

    # Create platform: Yes
    child.expect_exact("> ")
    child.sendline("1")

    # Sensor not found: Create
    child.expect_exact("Sensor 'GPS' on platform 'NELSON' not found.")
    child.sendline("1")

    # Enter name: (accept default)
    child.expect_exact("Please enter a name")
    child.sendline("")

    # Select classification: Public
    child.expect_exact("> ")
    child.sendline("2")

    # Create sensor: Yes
    child.expect_exact("> ")
    child.sendline("1")

    # What to import: Metadata and measurements
    child.expect_exact("Import metadata and measurements")
    import_output = child.before
    child.sendline("2")

    # Check number of files processed
    child.expect_exact("Files got processed: 1 times")

    # Expect end of output
    child.expect(pexpect.EOF)

    child.close()

    # Run a regex on the status output printed out after the import, to check that
    # we imported the correct number of States
    match = re.search(r"States \ +\|\ +(\d+) ", import_output)
    assert int(match.group(1)) == 5
