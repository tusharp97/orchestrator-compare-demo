import json
import logging
import os
from datetime import timedelta
from pathlib import Path

import duckdb
import pendulum
from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/demo/dbt_project")
DATA_DIR = Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data"))
DBT_COMMON = (
    f"--project-dir {PROJECT_DIR} --profiles-dir {PROJECT_DIR} "
    "--target-path /tmp/dbt-target --log-path /tmp/dbt-logs"
)


@dag(
    dag_id="shop_revenue_pipeline",
    description="Portable dbt pipeline used to compare Airflow with Dagster",
    schedule="*/5 * * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=False,
    default_args={
        "owner": "demo",
        "retries": 1,
        "retry_delay": timedelta(seconds=15),
    },
    tags=["demo", "dbt", "duckdb"],
)
def shop_revenue_pipeline():
    seed = BashOperator(
        task_id="load_seed_data",
        bash_command=f"dbt seed {DBT_COMMON} --full-refresh",
    )

    transform = BashOperator(
        task_id="transform_with_dbt",
        bash_command=f"dbt run {DBT_COMMON}",
    )

    test = BashOperator(
        task_id="test_with_dbt",
        bash_command=f"dbt test {DBT_COMMON}",
    )

    @task(task_id="publish_summary")
    def publish_summary() -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        database = os.environ["DUCKDB_PATH"]
        with duckdb.connect(database, read_only=True) as connection:
            rows = connection.execute(
                """
                select order_date, order_count, customer_count, gross_revenue
                from fct_daily_revenue
                order by order_date
                """
            ).fetchall()

        summary = {
            "orchestrator": "airflow",
            "database": database,
            "daily_revenue": [
                {
                    "order_date": str(row[0]),
                    "order_count": row[1],
                    "customer_count": row[2],
                    "gross_revenue": float(row[3]),
                }
                for row in rows
            ],
        }
        report_path = DATA_DIR / "airflow-summary.json"
        report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logging.info("Revenue summary: %s", json.dumps(summary))
        return summary

    seed >> transform >> test >> publish_summary()


shop_revenue_pipeline()
