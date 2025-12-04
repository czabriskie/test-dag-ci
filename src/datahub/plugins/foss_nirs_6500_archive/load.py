"""Parse Thermofisher Nanodrop files to .asm."""

from typing import Any, Union

from zontal_airflow_datahub.decorators import dag
from zontal_airflow_datahub.operators import asm, asm_setup, kubernetes
from zontal_airflow_space.operators import space

from applications.spectrophotometry.versions import FOSS_NIRS_6500_IMAGE

DAG_ID = "foss_nirs_6500_archive.load"
PARSER_NAME = "foss_nirs_6500"


def extract_metadata(asm_files: Union[str, list[str]]) -> dict[str, Any]:
    """Transform metadata to meet customer specifications."""
    return asm.extract_metadata(asm_files)


@dag.datahub_loader(DAG_ID,  tags=["spectrophotometry", "application"])
def process_archived():
    """."""
    # Create tasks
    parameters = asm_setup.evaluate_parameters("*.txt", include_dirs=False)
    vnf_information_package_profile = parameters["vnf_information_package_profile"]
    raw_files = parameters["raw_files"]
    asm_files = parameters["asm_files"]
    parser_args = asm_setup.zip_parser_arguments(raw_files, asm_files)
    parsed_raw = kubernetes.parse_raw(parser_args, PARSER_NAME, FOSS_NIRS_6500_IMAGE)
    ingested_asm = space.ingest(
        vnf_information_package_profile,
        asm_files,
        extract_metadata,
        asm_files,
    )
    updated_metadata = space.update_metadata(extract_metadata, asm_files)

    # Task flow
    parameters >> parsed_raw >> [updated_metadata, ingested_asm]


process_archived()
