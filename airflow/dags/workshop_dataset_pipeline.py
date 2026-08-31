import os
from pathlib import Path

import pendulum
from airflow.datasets import Dataset
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/demo/dbt_project")
DATA_DIR = Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data"))
READY_DATASET = Dataset("file:///opt/demo/data/orders-ready.flag")
DBT_COMMON = (
    f"--project-dir {PROJECT_DIR} --profiles-dir {PROJECT_DIR} "
    "--target-path /tmp/dbt-target --log-path /tmp/dbt-logs"
)


@dag(
    dag_id="workshop_dataset_producer",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["workshop", "dataset", "producer"],
)
def dataset_producer():
    @task(outlets=[READY_DATASET])
    def publish_orders_dataset() -> str:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        marker = DATA_DIR / "orders-ready.flag"
        marker.write_text("orders dataset is ready\n", encoding="utf-8")
        return str(marker)

    publish_orders_dataset()


@dag(
    dag_id="workshop_dataset_consumer",
    schedule=[READY_DATASET],
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=True,
    tags=["workshop", "dataset", "consumer"],
)
def dataset_consumer():
    BashOperator(
        task_id="build_marts_after_dataset_update",
        bash_command=f"dbt build {DBT_COMMON} --selector marts",
    )


dataset_producer()
dataset_consumer()
