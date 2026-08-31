import os
import subprocess
from pathlib import Path

from prefect import flow, task

PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/demo/dbt_project")
DBT_COMMON = [
    "--project-dir",
    PROJECT_DIR,
    "--profiles-dir",
    os.environ.get("DBT_PROFILES_DIR", PROJECT_DIR),
    "--target-path",
    "/tmp/dbt-target",
    "--log-path",
    "/tmp/dbt-logs",
]


@task(name="load_seed_data")
def load_seed_data() -> None:
    subprocess.run(["dbt", "seed", *DBT_COMMON, "--full-refresh"], check=True)


@task(name="transform_with_dbt")
def transform_with_dbt() -> None:
    subprocess.run(["dbt", "run", *DBT_COMMON], check=True)


@task(name="test_with_dbt")
def test_with_dbt() -> None:
    subprocess.run(["dbt", "test", *DBT_COMMON], check=True)


@task(name="publish_summary")
def publish_summary() -> None:
    script = Path("/opt/demo/scripts/publish_summary.py")
    subprocess.run(["python", str(script)], check=True)


@flow(name="shop-revenue-pipeline")
def shop_revenue_pipeline() -> None:
    Path("/tmp/dbt-target").mkdir(parents=True, exist_ok=True)
    Path("/tmp/dbt-logs").mkdir(parents=True, exist_ok=True)
    Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data")).mkdir(parents=True, exist_ok=True)
    load_seed_data()
    transform_with_dbt()
    test_with_dbt()
    publish_summary()


if __name__ == "__main__":
    shop_revenue_pipeline()
