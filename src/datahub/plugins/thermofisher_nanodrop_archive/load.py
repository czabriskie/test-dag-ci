"""Parse Thermofisher Nanodrop files to .asm."""

from typing import Any, Union

from zontal_airflow_datahub.decorators import dag
from zontal_airflow_datahub.operators import asm, asm_setup, kubernetes
from zontal_airflow_space.operators import space

from applications.spectrophotometry.versions import THERMOFISHER_NANODROP_IMAGE

DAG_ID = "thermofisher_nanodrop_archive.load"
PARSER_NAME = "thermofisher_nanodrop"


def extract_metadata(asm_files: Union[str, list[str]]) -> dict[str, Any]:
    """Transform metadata to meet customer specifications."""
    metadata = asm.extract_metadata(asm_files)
    final_metadata: dict[str, Any] = {}
    if metadata:
        # Define common key prefixes to avoid repetition
        device_doc = "experiment_document.device_system_document"

        final_metadata["model_number"] = metadata.get(f"{device_doc}.model_number")  # str
        final_metadata["device_identifier"] = metadata.get(f"{device_doc}.device_identifier")  # str
        final_metadata["equipment_serial_number"] = metadata.get(f"{device_doc}.equipment_serial_number")  # str

    return final_metadata


@dag.datahub_loader(DAG_ID,  tags=["spectrophotometry", "application"])
def process_archived():
    """."""
    # Create tasks
    import sys

    # Sometimes exceeds the python default recursion limit in the datahub loader
    sys.setrecursionlimit(2000)
    file_list = [f"*.{ext}" for ext in ["txt", "csv", "ndj", "tsv", "nd8"]]
    parameters = asm_setup.evaluate_parameters(file_list, include_dirs=False, include_files=True)
    vnf_information_package_profile = parameters["vnf_information_package_profile"]
    raw_files = parameters["raw_files"]
    asm_files = parameters["asm_files"]
    parser_args = asm_setup.zip_parser_arguments(raw_files, asm_files)
    parsed_raw = kubernetes.parse_raw(parser_args, PARSER_NAME, THERMOFISHER_NANODROP_IMAGE)
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
