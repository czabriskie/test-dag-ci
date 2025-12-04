"""Mock Spectrophotometry Operators."""

import os
from collections.abc import Sequence
from pathlib import Path

import boto3  # type: ignore[import-untyped]
from airflow.models.xcom_arg import XComArg
from airflow.utils.weight_rule import WeightRule
from zontal_airflow_datahub.decorators import task
from zontal_parser_sdk import pull_image

PARSE_RAW_PATH = "zontal_airflow_datahub.operators.kubernetes.parse_raw"
ASM_LOADER_PATH = (
    "zontal_airflow_datahub.operators.asm_operators.create_asm_loader_with_operator"
)


def patch_parse_raw(monkeypatch):
    """Mock KubernetesPodOperator using DockerOperator."""
    monkeypatch.setattr(PARSE_RAW_PATH, parse_raw)


def parse_raw(
    arguments: Sequence[tuple[str, str]], _parser_name: str, image: str
) -> XComArg:
    """Parse Spectrophotometry file formats to .asm.

    Args:
        arguments (Sequence[tuple[str, str]]): List of (raw_file, asm_file) tuples
        parser_name (str): The parser name, ignored for this mock
        image (str: optional): The relative image path in the registry
    """
    import subprocess

    ecr_registry = os.environ.get("ECR_REGISTRY")
    if ecr_registry:
        docker_image = f"{ecr_registry}/{image}"
    else:
        account_id = boto3.client("sts").get_caller_identity().get("Account")
        region = boto3.session.Session().region_name
        docker_image = f"{account_id}.dkr.ecr.{region}.amazonaws.com/{image}"

    pull_image(docker_image)

    @task.bash(task_id="parse_raw", weight_rule=WeightRule.UPSTREAM)
    def parse_raw_docker(arguments: tuple[str, str], docker_image: str):
        """Parse magellan file formats to .asm using docker."""
        raw_file_path = Path(arguments[0]).absolute()
        raw_file_name = raw_file_path.name
        asm_file_path = Path(arguments[1]).absolute()
        asm_file_name = asm_file_path.name
        cwd_path = raw_file_path.parent
        extra_args = arguments[2:]

        return subprocess.list2cmdline(
            [
                "docker",
                "run",
                "-u",
                "$(id -u):$(id -g)",
                "--platform",
                "linux/amd64",
                "-v",
                f"{cwd_path}:/input",
                "-w",
                "/input",
                docker_image,
                f"/input/{raw_file_name}",
                f"/input/{asm_file_name}",
                *extra_args,
            ]
        )

    return parse_raw_docker.partial(docker_image=docker_image).expand(
        arguments=arguments
    )
