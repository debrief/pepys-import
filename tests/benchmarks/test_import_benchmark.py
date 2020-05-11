import os

import pytest

from pepys_import.core.store.data_store import DataStore
from pepys_import.file.file_processor import FileProcessor
from tests.benchmarks.benchmark_utils import running_on_travis

FILE_DIR = os.path.dirname(__file__)


def run_import(processor, file_path):
    store = DataStore("", "", "", 0, ":memory:", db_type="sqlite")
    store.initialise()

    processor.process(file_path, store, False)


@pytest.mark.benchmark(min_time=0.1, max_time=2.0, min_rounds=10, warmup=False)
def test_single_rep_file_import_short(benchmark):
    processor = FileProcessor(archive=False)
    processor.load_importers_dynamically()

    benchmark(
        run_import,
        processor=processor,
        file_path=os.path.join(FILE_DIR, "benchmark_data/rep_test1.rep"),
    )

    if running_on_travis():
        if benchmark.stats.stats.mean > 0.3:
            pytest.fail(
                f"Mean benchmark run time of {benchmark.stats.stats.mean}s exceeded maximum time of 0.3s"
            )


@pytest.mark.benchmark(min_rounds=1, max_time=2.0, warmup=False)
def test_single_rep_file_import_long(benchmark):
    processor = FileProcessor(archive=False)
    processor.load_importers_dynamically()

    benchmark.pedantic(
        run_import,
        args=(processor, os.path.join(FILE_DIR, "benchmark_data/bulk_data.rep"),),
        iterations=1,
        rounds=1,
    )

    if running_on_travis():
        if benchmark.stats.stats.mean > 105:
            pytest.fail(
                f"Mean benchmark run time of {benchmark.stats.stats.mean}s exceeded maximum time of 105s"
            )
