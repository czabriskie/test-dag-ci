"""Parse spectrophotometry files to .asm."""

import pytest
from zontal_airflow.pytest.dags import assert_state, run_dag
from zontal_airflow_space.pytest import setup_information_package

from tests.mock_operators import patch_parse_raw

# to add more datasets, add the file to the list of the appropriate parser name
# to add a new parser test, add a new key value pair to the DATASETS dict
DATASETS = {
    "foss_nirs_6500": ["Acetone_2.txt.zip"],
    "thermofisher_nanodrop": ["dsDNA 08-Dec-2023 13_38_55.csv.zip"],
}


@pytest.fixture(autouse=True)
def _setup(monkeypatch, request):
    """."""
    source_file = request.param
    setup_information_package(
        "spectrophotometry_dags_archive",
        source_file,
    )
    patch_parse_raw(monkeypatch)


@pytest.mark.parametrize(
    ("_setup", "get_dag"),
    [
        pytest.param(
            f"src/tests/testdatasets/{parser_name}/{test_file}",
            f"datahub.plugins.{parser_name}_archive.load.process_archived",
            id=f"{parser_name}_archive_{idx}",
        )
        for parser_name, test_files in DATASETS.items()
        for idx, test_file in enumerate(test_files)
    ],
    indirect=True,
)
def test_spectrophotometry_archive_dags(get_dag, dagrun_conf):
    """Test the Space Plugin."""
    # Run DAG
    dagrun = run_dag(get_dag, run_conf=dagrun_conf)

    assert_state(
        dagrun,
        [
            "parameters",
            "zip_parser_arguments",
            "parsed_raw",
            "ingested_asm",
            "updated_metadata",
        ]
    )
