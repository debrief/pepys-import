==========================
Importer development guide
==========================

Introduction to import process & data flow
------------------------------------------

When a set of files are imported into the database using the :doc:`pepys-import
command-line interface </usage>`, the following process is carried out:

1. The command-line interface connects to the database (using the details in the
   :doc:`configuration` file) and loads all of the available importers (both those
   provided with pepys-import, and any local importers in the folder specified in
   the configuration file)

2. The File Processor finds all the files in the specified path, and processes
   these files in turn.

3. The File Processor looks through all the available importers and asks each
   importer in turn if it can process the file (based on the file extension, name,
   first line and contents, in turn). It keeps a list of all importers that would
   work on that specific file (as multiple importers can import a single file)

4. Each importer in the list is run separately on the file, and this is repeated
   for each file.

5. When the importer wants to add data to the database, it adds measurement
   objects (such as State or Contact) to a list of measurements that are stored
   temporarily (ie. not inserted directly into the database).

6. If all importers on the file complete with no errors, then the measurements
   are inserted into the database. Otherwise, an output file is written with the
   errors and no database insertion takes place.

The vast majority of this process is managed by the code in pepys-import itself:
the only part that a importer author needs to write themselves is the actual
parsing code (step 4), which creates measurements in the temporary storage area
(step 5).

The Importer class
------------------

Various examples of importer code are shown in the documentation below. A
relatively simple importer is the
:class:`.ETracImporter`
(:code:`importers/e_trac_importer.py`), and it may be useful to read its
source-code along with the following documentation.

A pepys-import importer is implemented as a class which inherits from the
Importer base-class. This class must implement various methods which are used to
find out which files this importer can process and then to actually do the
importing. These are defined, with comments, in the base :class:`.Importer` class
(:code:`pepys_import/file/importer.py`). A summary of the methods which must be
implemented is below:

+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| Method                            | Description                                                                                                                |
+===================================+============================================================================================================================+
| :code:`__init__`                  | Initialises the class. Must call the :code:`super().__init__` method to set various key class parameters                   |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`can_load_this_type`        | Checks the file extension (‘suffix’) provided and returns True if it can import that type of file, otherwise returns False |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`can_load_this_filename`    | Checks the filename and returns True if it can import a file with that filename, otherwise returns False                   |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`can_load_this_header`      | Checks the first line of the file and returns True if it can import a file with that header, otherwise returns False       |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`can_load_this_file`        | Checks the entire file contents and returns True if it can import that file, otherwise returns False                       |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`_load_this_line`           | Imports data from a single line in a file. Either this method or :code:`_load_this_file` must be overriden.                |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+
| :code:`_load_this_file`           | Imports data from the entire file.                                                                                         |
+-----------------------------------+----------------------------------------------------------------------------------------------------------------------------+

Initialisation
##############

The :code:`__init__` method must be defined, taking the arguments listed below,
and the :code:`super().__init__()` method must be called.

+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Argument                  | Description                                                                                                                                                                                                                                                             |
+===========================+=========================================================================================================================================================================================================================================================================+
| :code:`name`              | Full name for the parser - used where space isn’t a problem, so can be reasonably long                                                                                                                                                                                  |
+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| :code:`short_name`        | Short name for the parser - used in error lists and other places - so should be relatively short                                                                                                                                                                        |
+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| :code:`validation_level`  | Defines the level of validation required for this parser. Must be one of :code:`pepys_import.core.validators.constants.NONE_LEVEL`, :code:`pepys_import.core.validators.constants.BASIC_LEVEL`, or :code:`pepys_import.core.validators.constants.ENHANCED_LEVEL`        |
+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| :code:`default_privacy`   | (Optional) Defines the hardcoded privacy level of all data coming from this importer. Defaults to None, which means the user is asked for the privacy.                                                                                                                  |
+---------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

A complete example is:

.. code-block:: python

    def __init__(
            self,
            name="Example File Format Importer",
            validation_level=constants.ENHANCED_LEVEL,
            short_name="Example Importer",
        ):
            super().__init__(name, validation_level, short_name)


Parser check methods
####################

The File Processor checks each of the can_load_this_x methods to determine
whether the importer can load a specific file. They are checked in the following
order:

* Type
* Filename
* Header
* File

If it is impossible to tell if a file can be loaded based on the information
provided then these methods should just return :code:`True`. For example, the
:class:`.GPXImporter` can import files with an extension
:code:`.gpx`, so has some logic in the :code:`can_load_type` method, but just returns
:code:`True` for all other checking methods.

Loading methods
###############

Many importers operate on a line-by-line basis (for example, a CSV-style
importer which reads each line separately) but some parsers need access to the
whole file at one time (for example, an XML-style importer which needs to parse
the whole document in one operation). To accommodate these two styles of
parsing, there are two methods. One, and only one, of these methods should be
implemented by importer classes.

:meth:`._load_this_line` is passed a single line and
should process the line and create any measurement objects that are needed. Code
in the implementation of the :meth:`._load_this_file`
method in the base :class:`.Importer` class is
responsible for iterating over the lines in the file and calling
:meth:`._load_this_line` once for each line.
Alternatively, :meth:`._load_this_file` itself can be
implemented in the subclass, and this is passed an entire file which it can
process in any way it wants.

It is possible to process files where the data for one measurement instance is
split across multiple lines by implementing
:meth:`._load_this_line` - data should be stored in
instance variables when it appears, and then once all data is available a
measurement object should be created. For an example of this see the
:class:`.NMEAImporter` in :code:`importers/nmea_importer.py`.

Tokens and highlighting
#######################

A typical implementation of :meth:`._load_this_line`
would take the line provided, split it by some delimiter and then process each
separate token in the line. You may expect to use the standard Python functions
like :code:`split` to do this, but pepys-import also provides a more fully-featured way
of dealing with tokens and lines, which allows the export of highlighted HTML
files showing which parts of the file have been used to extract each individual
part field in the created measurements, and tracks the extraction in the
database to help understand data provenance.

But this token highlighting and database recording does come with
a performance cost. For high volume file types that are tightly
structured, with little room for misinterpretation, the overhead
may not be justified. You can configure the level of extraction that will
take place by calling :code:`self.set_highlighting_level()` in the :code:`__init__` method.
Three different values can be passed to this function: :code:`"none"` will turn off all extraction
and highlighting, :code:`"html"` will record extractions to HTML but not to the database, and
:code:`"database"` will record to both a HTML file and the database. The default is :code:`"html"`.

Similarly, it may be justified to capture extraction data in the early stages of
developing/maintaining the parser for a new file format, with level of
extraction recording reduced as it matures.

The line parameter passed to :meth:`._load_this_line`
is actually a :class:`.Line` object,
from which a list of tokens can be produced using the
:meth:`~.Line.tokens` method. This takes a regular expression,

The text of each Token/Line object can be accessed as :code:`Token.text`, so the
following two code examples are equivalent:

.. code-block:: python

    # Basic Python
    # (default separator is any whitespace)
    tokens = line.split()
    print(tokens[1])

    # Pepys-import methods
    Tokens = line.tokens(line.WHITESPACE_TOKENISER)
    print(tokens[1].text)

The argument to :meth:`~.Line.tokens` is a regular expression giving the parts of the line
to extract as tokens (*not* the parts of the line to use as a separator). Various useful
regular expressions are defined in the line class including :code:`WHITESPACE_TOKENISER`
and :code:`CSV_TOKENISER`. As an example, the :code:`WHITESPACE_TOKENISER` is :code:`\S+`,
which matches one or more non-whitespace characters, which is what defines a token if the
separator is whitespace.

Tokens and Lines also have a
:meth:`~.Line.record` method, which is
used to record that a particular extraction was performed using that token. This
will then be represented as a highlighted region in the output HTML. The record
method takes arguments of the name of the parser (should always be set to
:code:`self.name`), the name of the field that was extracted and the parsed
value. It also takes an optional units argument, for use when units cannot be
explicitly specified (see the :ref:`units` section). For example:

.. code-block:: python

    comp_name_token = tokens[18]
    vessel_name = comp_name_token.text.upper()
    comp_name_token.record(self.name, "vessel name", vessel_name)

The :func:`.combine_tokens`
function can be used to combine two disparate tokens into one new token, so that
one extraction can be recorded from disparate data in the file. For example:

.. code-block:: python

    combine_tokens(long_degrees_token, lat_degrees_token).record(
        self.name, "location", state.location, "decimal degrees")

Once token extractions have been recorded using the :code:`record` method, the recorded information
must be linked to the appropriate measurement object (State/Contact/Comment etc) and prepared for saving
to the database. This can be done using the :code:`Datafile.flush_extracted_tokens` method, which should be called once
all the data has been loaded for a specific measurement object. Usually this will be at the end of the
:meth:`~pepys_import.file.importer._load_this_line` method, or at the end of a loop inside the
:meth:`~pepys_import.file.importer._load_this_file` method - but for complex importers it may be elsewhere.


Creating measurement objects
############################

Both :meth:`~pepys_import.file.importer._load_this_line` and
:meth:`~pepys_import.file.importer._load_this_file` are passed a
:class:`.Datafile` object by the File Processor. This can be used to create
measurement objects using the :meth:`.create_state`, :meth:`.create_contact` or
:meth:`.create_comment` methods. These methods require arguments for the
:code:`data_store` (provided by the File Processor), :code:`platform`,
:code:`sensor`, :code:`timestamp` and the :code:`parser_name` (always
:code:`self.short_name`).

The platform can be obtained from
:code:`data_store.get_platform` and the sensor from :code:`platform.get_sensor`.
The timestamp must be parsed from the file.

Where the value for a field is missing, Pepys will use command-line interaction
to get this data from the current user. It will also ensure that supporting
metadata is also determined (such as the nationality for a new platform).

In most circumstances, a file will only contain information on the name of the
platform (eg. :code:`DOLPHIN`) and not the nationality or identifier. As the
combination of all three of these are required to uniquely identify a platform,
we have to 'resolve' it via user interaction to establish which platform this
name refers to. Doing this repeatedly for every line of a file would require
a lot of user interaction, and a particular platform name in a file is likely
to refer to the same platform throughout the file. Therefore, we can use the
:code:`self.get_cached_platform` method instead of the :code:`data_store.get_platform`
method. This tries to look in a cache which links platform names from the file
to actual Platform entries, and if it can't find it in the cache then it resolves
it as usual. The cache is reset every time a new file is processed - meaning
the user should only have to interact to identify the platform once per platform, per file.

Similarly, a :code:`self.get_cached_sensor` method exists, which can be used to cache
the sensor associated with a platform, to reduce the need for user interaction to select
the sensor for each row of the data. This should be used for files where there is only
one sensor per platform in the file - for example, when the sensor is a location sensor
used to produce the location data which are being imported into State objects, and
is not listed in the file. However, this should not be used for files where the
sensors are specifically listed in the file - for example, those that import Contact objects.

For example:

.. code-block:: python

    # Get the platform given the vessel_name (a variable parsed from the file earlier in the code)
    platform = self.get_cached_platform(
            data_store, platform_name=vessel_name, change_id=change_id
        )

    sensor = self.get_cached_sensor(
                data_store=data_store,
                sensor_name=None,
                sensor_type=None,
                platform_id=platform.platform_id,
                change_id=change_id,
            )

    # Create the actual state object
    state = datafile.create_state(data_store, platform, sensor, timestamp, self.short_name)
    # Set the privacy
    state.privacy = privacy.privacy_id

    # Now we can set state properties
    state.location = ...

As metadata is created (such as platform or sensor) it is added directly to the
database, to ease streamline re-loading the file if parsing later fails.

But, once a measurement (state, contact, or comment) is created using the
:code:`datafile.create_x` method, it is added to the list of pending measurements stored
in the File Processor - therefore nothing else needs doing to ‘commit’ the
measurement, and the function body can finish immediately after assigning all of
the measurement properties. Once all of the relevant parsers have run on a file,
and data validation tests pass, the data is submitted to the database.

.. _units:

Setting measurement object properties with units
################################################

All properties on measurement objects (states, contacts or comments) can be set
in the standard Python way as :code:`state.speed = <variable>`. However, properties that
have units associated with them (for example, :code:`state.speed`, :code:`state.elevation`,
:code:`contact.bearing`, :code:`contact.orientation`) must be set to a value with associated
units. These are provided through the `pint
<https://pint.readthedocs.io/>`_ Python package, which provides a
:code:`unit_registry` (available as :code:`pepys_import.core.formats.unit_registry`) containing
objects for all units. A value can be given units by multiplying it by a unit
object, for example:

.. code-block:: python

    # 5 knots
    speed = 5 * unit_registry.knot

    # 157 degrees
    bearing = 157 * unit_registry.degree

The resulting value is a :code:`Quantity` (an object type provided by pint) which stores
both the numerical value along with the unit, and provides helpful methods for
converting to different units.

In the context of an importer, code like the following may be used:

.. code-block:: python

    state.elevation = altitude_token.text * unit_registry.metre

A more robust approach is given by using the conversion functions provided in
:code:`pepys_import/utils/unit_utils.py`, such as :func:`.convert_absolute_angle` and
:func:`.convert_speed`. These take a string value and a unit, and attempt to convert the
string value to a float (storing an error if this fails) and then set the
relevant unit (either the unit passed to the function, or the default unit for
values that are only ever provided in a single unit, such as angles).

Setting location properties
###########################

Some of the most common errors in this sort of data processing are errors in
storing location data - for example, mixing up latitude and longitude, or errors
parsing values given in ‘degrees, minutes, seconds’ (DMS) format. Therefore,
pepys-import has a verbose but clear way of setting location values using the
:class:`.Location` class.

The :class.`Location` class stores a latitude and longitude in decimal degrees, but
allows setting these values in both decimal degrees and DMS. The class should be
initialised as:

.. code-block:: python

    location = Location(errors=self.errors, error_type=self.error_type)

as this allows any errors from parsing locations to be reported (see the :ref:`errors` section).
Then methods like :meth:`.set_latitude_decimal_degrees` or :meth:`.set_longitude_dms` can be used to
set values based on values in the input file. Finally, the :code:`state.location` property should be
set to the instance of the :class:`.Location` class. For example:

.. code-block:: python

    location = Location(errors=self.errors, error_type=self.error_type)
    location.set_latitude_decimal_degrees(lat_degrees_token.text)
    location.set_longitude_decimal_degrees(long_degrees_token.text)

    state.location = location

.. _errors:

Storing errors
##############

Various errors can be found while parsing a document - for example, a missing
field, or an invalid numerical value. These need to be stored so that they can
be reported to the user - and used to stop the actual import to the database
occurring if there are errors.

Errors should be stored in the :code:`self.errors` list, where each item in the list is
a dictionary where the key is the ‘error type’ and the value is a string
describing the error. The ‘error type’ is automatically defined by the class
initialisation to be a string of the form :code:`"{self.short_name} - Parsing error on
{basename}"`, and this is stored in :code:`self.error_type`, so errors can be added as in
the example below:

.. code-block:: python

    self.errors.append(
        {
            self.error_type: f"Line {line_number}. Error in Date format '{time_token.text}'."
            "Should be HH:mm:ss"
        }
    )

Parser development environment and testing
------------------------------------------

Ensure development environment is set up correctly
##################################################
The deployed version of pepys-import contains all the development dependencies, except for a local
install of PostgreSQL. To check everything is set up correctly, run all the tests _excluding_ those
that require PostgreSQL by following these steps:

1. Open a Windows Command Prompt
2. Change to the directory containing the pepys-import installation
3. Run :code:`cd bin` to change to the bin directory
4. Run :code:`set_paths.bat` to set up the relevant paths to Python and its dependencies
5. Run :code:`cd ..` to change back to the main directory
6. Run :code:`python -m pytest tests/ -m "not postgres"` to run all tests excluding the PostgreSQL tests

Start developing parser
#######################

Obtain or create an example file in the new format - ideally one that covers as many of the
variations in the format as possible.

Start writing a new :class:`.Importer` subclass using the instructions above. Name the importer file
:code:`format_importer.py` (for example, :code:`gpx_importer.py`) and place it in a directory of
your choice (you will set the configuration to allow pepys-import to pick up this importer in the
:ref:`how-to-deploy-parser` section below).

Create test for new parser
##########################

Create a new file called :code:`test_load_FORMAT.py`. This can be located anywhere you want, but a
sensible place to put it would be in the same folder as the new importer.

Copy into this file the basic test structure from one of the existing test files (for example
:code:`tests/test_load_gpx.py`) and edit to load the sample data file (change :code:`DATA_PATH`) and
to register the new :class:`.Importer` subclass (the :code:`processor.register_importer` line). Also
change the definition of :code:`self.store` to be a :class:`.DataStore` backed by a local SQLite
database file, for example:

.. code-block:: python

    self.store = DataStore("", "", "", 0, "test.db", db_type="sqlite")

Comment out the actual assert statements in the test. You can then use this test as a test while
developing the new importer by running the test as:

.. code-block:: shell

    python -m pytest test_load_blah.py -s

This will show all stdout output, so you can see debugging print statements that you may have used
in the importer. If you want to debug at a particular point in the importer then add a line
containing :code:`breakpoint()` at the relevant location, and run pytest with the :code:`--pdb` flag.

The data will be imported into a SQLite database called :code:`test.db` in the same folder as the
Importer python file, and this can be viewed using something like (`SQLite Studio
<https://sqlitestudio.pl/index.rvt?act=download>`__)

Once the importer is working, uncomment the assert statements and update the tests for the number of
states, platforms and datafiles that should be added, plus add some tests for specific values that
should be present in the imported data.

.. _how-to-deploy-parser:

How to deploy a parser
----------------------

Set the parsers configuration option in the :code:`[local]` section of the pepys-import
:doc:`configuration` file to point to a directory to hold custom local importers. Place the new
importer in this folder: it should now be picked up by pepys-import.

To test this, run the pepys-import import CLI with the :code:`--db test.db` option, to do an import to a
local SQLite database.

Helpful recipes
===============

Skipping a line in a file
-------------------------

The return statement in :meth:`._load_this_line` returns from the function which is processing that
specific line, and then moves on to the next line - therefore it is equivalent to the :code:`continue`
statement in a standard for loop.

If you want to skip a specific line then a :code:`line_number` argument is passed to
:meth:`._load_this_line`, so this can be done by:

.. code-block:: python

    # Skip the header line (can do this with any if statement)
    if line_number == 1:
        return

