import logging
import os
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.python import PythonSensor

DATA_DIR = Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data"))


def log_success(context) -> None:
    logging.info("Workshop master succeeded: %s", context["run_id"])


def log_failure(context) -> None:
    logging.error("Workshop master failed: %s", context["run_id"])


with DAG(
    dag_id="workshop_master_sensor",
    description="Sensor plus parent/child DAG orchestration and callbacks.",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=True,
    on_success_callback=log_success,
    on_failure_callback=log_failure,
    tags=["workshop", "sensor", "trigger-dag", "callbacks"],
    doc_md="""
Create `/opt/demo/data/orders-ready.flag` by triggering
`workshop_dataset_producer`, then this DAG detects it and synchronously triggers
the metadata-generated `workshop_dbt_marts` child DAG.
""",
) as dag:
    start = EmptyOperator(task_id="start")

    wait_for_orders = PythonSensor(
        task_id="wait_for_orders_ready_file",
        python_callable=lambda: (DATA_DIR / "orders-ready.flag").exists(),
        poke_interval=5,
        timeout=180,
        mode="reschedule",
    )

    trigger_marts = TriggerDagRunOperator(
        task_id="trigger_marts_child_dag",
        trigger_dag_id="workshop_dbt_marts",
        trigger_run_id="master__{{ ts_nodash }}",
        wait_for_completion=True,
        poke_interval=5,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    end = EmptyOperator(task_id="end")
    start >> wait_for_orders >> trigger_marts >> end
