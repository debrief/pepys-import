import os

from pepys_import.utils.import_utils import sort_files

FILE_PATH = os.path.dirname(__file__)
DATA_PATH = os.path.join(FILE_PATH, "sample_data")
GPX_DATA_PATH = os.path.join(DATA_PATH, "track_files", "gpx")


def test_sort_files():
    normal_result = []
    for f in os.scandir(GPX_DATA_PATH):
        normal_result.append(f.name)
    sorted_result = []
    for f in sort_files(os.scandir(GPX_DATA_PATH)):
        sorted_result.append(f.name)

    assert sorted(normal_result) == sorted_result
