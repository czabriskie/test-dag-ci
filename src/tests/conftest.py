"""Configure Airflow for tests."""

import importlib

import pytest
from zontal_airflow.pytest import get_test_dagrun_conf
from zontal_airflow_datahub.pytest import init_airflow_datahub_pytest


@pytest.fixture
def dagrun_conf():
    """DAG Run configuration used by run_task and run_dag.

    Populated by setup_information_package and activate_information_package.
    """
    return get_test_dagrun_conf()


def pytest_configure() -> None:
    """Configure test environment."""
    # Configure Airflow for tests
    init_airflow_datahub_pytest("spectrophotometry_dags")


@pytest.fixture
def get_dag(request):
    """Fixture to get the DAG function."""
    dag_path = request.param
    module_name, function_name = dag_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)
