import os

from pepys_import.file.highlighter.highlighter import HighlightedFile
from pepys_import.file.highlighter.xml_parser import parse

FILE_PATH = os.path.dirname(__file__)
ASCII_GPX_PATH = os.path.join(FILE_PATH, "sample_data/track_files/gpx/gpx_1_0.gpx")
UNICODE_GPX_PATH = os.path.join(FILE_PATH, "sample_data/track_files/gpx/gpx_1_0_Unicode.gpx")


def test_parser_returns_correct_tree():
    # General test that normal XML operations work fine with our custom parser
    doc = parse(ASCII_GPX_PATH)

    assert len(doc.findall(".//{*}trk")) == 1
    trkpts = doc.findall(".//{*}trkpt")
    assert len(trkpts) == 5

    assert trkpts[0].attrib["lat"] == "22.1862861"
    # Counts children
    assert len(list(trkpts[0])) == 4

    elev_els = doc.findall(".//{*}ele")
    assert len(elev_els) == 5
    assert elev_els[0].text == "0.000"


def test_parser_source_line():
    hf = HighlightedFile(ASCII_GPX_PATH)

    doc = parse(ASCII_GPX_PATH, hf)

    trks = doc.findall(".//{*}trk")
    assert trks[0].sourceline == 10

    trkpts = doc.findall(".//{*}trkpt")
    assert trkpts[0].sourceline == 13

    elev_els = doc.findall(".//{*}ele")
    assert elev_els[0].sourceline == 14


def _check_element(el, file_contents):
    el_name = el.tag
    if "{" in el_name:
        el_name = el_name[el_name.find("}") + 1 :]

    # Check that the opening tag substring includes the name of the element, and starts
    # and ends with a < and > (ignoring whitespace)
    opening_tag_str = file_contents[el.opening_tag_start : el.opening_tag_end].strip()
    assert el_name in opening_tag_str
    assert opening_tag_str.startswith("<")
    assert opening_tag_str.endswith(">")

    # Check that the other substrings have valid indices (ie no IndexError raised)
    _ = file_contents[el.text_start : el.closing_tag_start]
    _ = file_contents[el.opening_tag_start : el.closing_tag_start]

    for child_el in el:
        _check_element(child_el, file_contents)


# This tests the raw byte indexes stored in the Element class
# We can't test this with unicode, as the conversion to actual character
# indexes only happens in the `record` method (to save computationally on doing)
# it for each element
def test_parser_returns_correct_byte_locations_ascii():
    with open(ASCII_GPX_PATH) as f:
        file_contents = f.read()

    doc = parse(ASCII_GPX_PATH)

    _check_element(doc.getroot(), file_contents)


def _check_element_record(el, file_contents):
    el_name = el.tag
    if "{" in el_name:
        el_name = el_name[el_name.find("}") + 1 :]

    start, end = el.record("tool", "field", "value", xml_part="opening")

    opening_tag_str = file_contents[start:end].strip()
    assert el_name in opening_tag_str
    assert opening_tag_str.startswith("<")
    assert opening_tag_str.endswith(">")

    for child_el in el:
        _check_element_record(child_el, file_contents)


class FakeDatafile:
    def __init__(self):
        self.pending_extracted_tokens = []


# To test with unicode we need to actually call the record method
# and then get the locations it's used out from there
def test_parser_record_works_correctly_unicode():
    with open(UNICODE_GPX_PATH, encoding="utf-8") as f:
        file_contents = f.read()

    hf = HighlightedFile(UNICODE_GPX_PATH)
    hf.datafile = FakeDatafile()

    doc = parse(UNICODE_GPX_PATH, hf)

    _check_element_record(doc.getroot(), file_contents)


def test_parser_record_works_correctly_ascii():
    with open(ASCII_GPX_PATH) as f:
        file_contents = f.read()

    hf = HighlightedFile(ASCII_GPX_PATH)
    hf.datafile = FakeDatafile()

    doc = parse(ASCII_GPX_PATH, hf)

    _check_element_record(doc.getroot(), file_contents)
