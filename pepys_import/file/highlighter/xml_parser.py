# The complex importing code that is the first ~10 lines of this file is needed
# because when you import xml.etree.ElementTree, Python automatically imports
# the C versions of these modules from the _elementtree C library. We can't use
# these versions we need to modify attributes that the C version doesn't provide
# access to.
# Normally, deleting _elementtree.XMLParser object works fine, as Python then can't
# find it, and so imports the Python version instead. However, if we're running within
# pytest then the XML ElementTree module will have already been imported by pytest,
# so we need to delete it from the list of imported modules, so we can import it
# ourselves without the C version being imported. Thus, the first try-except clause
# below is only needed when running with pytest, and in other situations the module
# won't already be imported, so it will do nothing.
import sys

try:
    del sys.modules["xml.etree.ElementTree"]
except KeyError:
    pass

import _elementtree

try:
    del _elementtree.XMLParser
except AttributeError:
    # in case deleted twice
    pass

from xml.etree.ElementTree import Comment, Element, ProcessingInstruction, XMLParser
from xml.etree.ElementTree import parse as original_parse

from pepys_import.file.highlighter.support.usages import SingleUsage


class MyElement(Element):
    """
    A subclass of the Python ElementTree.Element class, which represents a
    XML element. This subclass has various additional member variables to
    store byte offsets for the element and can take an optional highlighted_file
    and/or start_byte argument in the constructor.

    Note: the offsets stored are *byte* offsets, not character offsets - so these
    cannot be used for indexing into a non-ASCII Python string unless you convert byte offsets
    to character offsets first.
    """

    def __init__(
        self, tag, attrib={}, highlighted_file=None, start_byte=None, line_number=None, **extra
    ):
        #
        # Example XML:
        #
        #   <tag attrib='blah'>text content here</tag>
        #   |                  |                |
        #   A                C & D              B
        #
        # (C and D can be in different places if there is a tag inside this one)
        #
        #
        # Stores the byte offset of the start of the opening tag (A in diagram)
        self.opening_tag_start = start_byte
        # Stores the byte offset of the start of the closing tag (B in diagram)
        self.closing_tag_start = None
        # Stores the byte offset of the start of the text content (C in diagram)
        self.text_start = None
        # Stores the byte offset of the end of the opening tag (D in diagram)
        self.opening_tag_end = None
        # Stores a highlighted_file instance, so that we can call .record on this element
        self.highlighted_file = highlighted_file

        # Store the line number too
        self.sourceline = line_number

        super(MyElement, self).__init__(tag, attrib, **extra)

    def record(self, tool: str, field: str, value: str, units: str = None, xml_part="text"):
        """
        Record the usage of this element for a specific purpose

        :param tool: Name of the importer handling the import (eg. "NMEA Importer)
                     Should be set to `self.name` when called from an importer
        :param field: The field that the token is being interpreted as (eg. "speed")
        :param value: The parsed value of the token (eg. "5 knots") - where possible,
                      pass a Quantity object with associated units
        :param units: The units that the field was interpreted as using (optional - do not
                      include if the value was a Quantity as that holds unit information itself
        :param xml_part: Specifies which bit of the XML for the element to record, must be either
                         "text" which records the text of the element, "opening" which records
                         the opening tag, or "all" which records the opening tag and text.

        """
        if self.highlighted_file is None:
            raise ValueError("No HighlightedFile instance is associated with this Element")

        self.highlighted_file.fill_char_array_if_needed()

        tool_field = tool + "/" + field
        if units is not None:
            message = "Value:" + str(value) + " Units:" + str(units)
        else:
            message = "Value:" + str(value)

        usage = SingleUsage(tool_field, message)

        if xml_part == "text":
            # Just record the text content of the tag
            # <tag>text here</tag>
            #      #########  <- recorded text
            start = self.text_start
            end = self.closing_tag_start
        elif xml_part == "opening":
            # Record the opening tag
            # <tag attrib='blah'>text here</tag>
            # ################### <- recorded text
            start = self.opening_tag_start
            end = self.opening_tag_end
        elif xml_part == "all":
            # Record the full XML element, excluding the closing tag
            # <tag attrib='blah'>text here</tag>
            # ############################ <- recorded text
            start = self.opening_tag_start
            end = self.closing_tag_start
        else:
            raise ValueError("Invalid xml_part. Must be one of 'text', 'opening', 'all'")

        # Convert from byte indexes to character indexes
        start_in_chars = len(self.highlighted_file.file_byte_contents[:start].decode())
        end_in_chars = start_in_chars + len(
            self.highlighted_file.file_byte_contents[start:end].decode()
        )

        text_location_str = f"{start_in_chars}-{end_in_chars}"
        text = self.highlighted_file.file_byte_contents[start:end].decode()

        self.highlighted_file.datafile.pending_extracted_tokens.append(
            {
                "text": text,
                "interpreted_value": str(value),
                "text_location": text_location_str,
                "importer": tool,
                "field": field,
            }
        )

        # This return returns the start and end index, mainly for use for testing
        return self.highlighted_file.set_usages_for_slice(start_in_chars, end_in_chars, usage)


class MyTreeBuilder:
    """
    Class used to build the tree structure of an XML file in memory,
    while keeping track of byte offsets to get XML element locations.

    Note: the majority of this is copied from the Python Standard Library
    TreeBuilder, but this has been extended to:
    - Store a parser instance from the constructor
    - Call self._parser.parser.CurrentByteIndex to get the byte index in
      methods like `start` and `end`
    - Pass this byte index to the MyElement constructor
    - Set the end and text_start locations in the MyElement constructor too

    Notes from original TreeBuilder docstring:

    This builder converts a sequence of start, data, and end method
    calls to a well-formed element structure.
    You can use this class to build an element structure using a custom XML
    parser, or a parser for some other XML-like format.
    *element_factory* is an optional element factory which is called
    to create new Element instances, as necessary.
    *comment_factory* is a factory to create comments to be used instead of
    the standard factory.  If *insert_comments* is false (the default),
    comments will not be inserted into the tree.
    *pi_factory* is a factory to create processing instructions to be used
    instead of the standard factory.  If *insert_pis* is false (the default),
    processing instructions will not be inserted into the tree.
    """

    def __init__(
        self,
        parser=None,
        highlighted_file=None,
        element_factory=None,
        *,
        comment_factory=None,
        pi_factory=None,
        insert_comments=False,
        insert_pis=False,
    ):
        self._parser = parser
        self._highlighted_file = highlighted_file
        self._data = []  # data collector
        self._elem = []  # element stack
        self._last = None  # last element
        self._root = None  # root element
        self._tail = None  # true if we're after an end tag
        if comment_factory is None:
            comment_factory = Comment
        self._comment_factory = comment_factory
        self.insert_comments = insert_comments
        if pi_factory is None:
            pi_factory = ProcessingInstruction
        self._pi_factory = pi_factory
        self.insert_pis = insert_pis
        if element_factory is None:
            element_factory = Element
        self._factory = element_factory

    def close(self):
        """Flush builder buffers and return toplevel document Element."""
        assert len(self._elem) == 0, "missing end tags"
        assert self._root is not None, "missing toplevel element"
        return self._root

    def _flush(self):
        if self._data:
            if self._last is not None:
                text = "".join(self._data)
                if self._tail:
                    assert self._last.tail is None, "internal error (tail)"
                    self._last.tail = text
                else:
                    assert self._last.text is None, "internal error (text)"
                    self._last.text = text
                    # We've got to the point when we actually set the .text attribute,
                    # so we need to set text_start too
                    self._last.text_start = self._data_start
            self._data = []

    def data(self, data):
        """Add text to current element."""
        if self._data == []:
            # If there's nothing currently in _data, it means that we're
            # starting a new element's text content
            if self._last is not None:
                if self._last.closing_tag_start is None:
                    # If we haven't closed the last tag yet, then as we've started text
                    # we must have finished the opening tag
                    self._last.opening_tag_end = self._parser.parser.CurrentByteIndex

            # Starting location of text
            self._data_start = self._parser.parser.CurrentByteIndex

        self._data.append(data)

    def start(self, tag, attrs):
        """Open new element and return it.
        *tag* is the element name, *attrs* is a dict containing element
        attributes.
        """
        self._flush()
        if self._last is not None:
            # We've started a new tag, so if we haven't already closed the last tag
            # then we need to mark the opening tag end
            if self._last.closing_tag_start is None:
                self._last.opening_tag_end = self._parser.parser.CurrentByteIndex
        self._last = elem = self._factory(
            tag,
            attrs,
            start_byte=self._parser.parser.CurrentByteIndex,  # Pass the current byte index in to constructor
            line_number=self._parser.parser.CurrentLineNumber,  # Pass the current line number in to the constructor
            highlighted_file=self._highlighted_file,
        )
        if self._elem:
            self._elem[-1].append(elem)
        elif self._root is None:
            self._root = elem
        self._elem.append(elem)
        self._tail = 0
        return elem

    def end(self, tag):
        """Close and return current Element.
        *tag* is the element name.
        """
        self._flush()
        self._last = self._elem.pop()

        # Record the start of the closing tag
        self._last.closing_tag_start = self._parser.parser.CurrentByteIndex

        if self._last.opening_tag_end is None:
            # If we haven't seen the end of the opening tag yet then
            # it is here
            self._last.opening_tag_end = self._last.closing_tag_start

        assert self._last.tag == tag, "end tag mismatch (expected %s, got %s)" % (
            self._last.tag,
            tag,
        )
        self._tail = 1
        return self._last

    def comment(self, text):
        """Create a comment using the comment_factory.
        *text* is the text of the comment.
        """
        return self._handle_single(self._comment_factory, self.insert_comments, text)

    def pi(self, target, text=None):
        """Create a processing instruction using the pi_factory.
        *target* is the target name of the processing instruction.
        *text* is the data of the processing instruction, or ''.
        """
        return self._handle_single(self._pi_factory, self.insert_pis, target, text)

    def _handle_single(self, factory, insert, *args):
        elem = factory(*args)
        if insert:
            self._flush()
            self._last = elem
            if self._elem:
                self._elem[-1].append(elem)
            self._tail = 1
        return elem


def parse(file_object, highlighted_file=None):
    """Parse an XML file using our custom parser functions that allow extraction
    of the locations of XML elements in the file, and the use of the `record` method
    to record extractions to a HighlightedFile instance.

    Arguments:
     - file_object: an open file object to read the XML from
     - highlighted_file (optional): A HighlightedFile instance initialised from the same
       file as the file object, used to record extractions.
    """

    # Create a parser instance without giving it a TreeBuilder class
    parser = XMLParser(target=None)

    # Create a MyTreeBuilder instance, passing in a reference to the parser
    # and the highlighted file, and using the MyElement class as the factory
    # to use to create element objects
    tree_builder = MyTreeBuilder(
        parser=parser, highlighted_file=highlighted_file, element_factory=MyElement
    )

    # Reinitialise the parser, now that we've created the right MyTreeBuilder object to pass
    # to it (this is needed as there is a circular reference between them: MyTreeBuilder needs
    # a reference to the parser, but the parser needs a reference to MyTreeBuilder)
    parser.__init__(target=tree_builder)

    # Tell it not to buffer text, otherwise we don't get proper events
    # for the start of each text segment
    parser.parser.buffer_text = False

    return original_parse(file_object, parser)
