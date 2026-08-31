import json
import os
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/demo/dbt_project")
CONFIG_PATH = Path(__file__).with_name("workshop_pipelines.json")
DBT_COMMON = (
    f"--project-dir {PROJECT_DIR} --profiles-dir {PROJECT_DIR} "
    "--target-path /tmp/dbt-target --log-path /tmp/dbt-logs"
)


def make_dag(config: dict) -> DAG:
    with DAG(
        dag_id=config["dag_id"],
        description=config["description"],
        schedule=config["schedule"],
        start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
        catchup=False,
        is_paused_upon_creation=True,
        default_args={
            "owner": "workshop",
            "retries": 1,
            "retry_delay": timedelta(seconds=15),
        },
        tags=["workshop", "dynamic-factory", f"selector:{config['selector']}"],
        doc_md=f"""
### Metadata-generated dbt DAG

This DAG is generated from `workshop_pipelines.json` and executes the
`{config["selector"]}` dbt selector. Add another JSON object to generate
another DAG without duplicating Python orchestration code.
""",
    ) as dag:
        BashOperator(
            task_id=f"dbt_build_{config['selector']}",
            bash_command=(
                f"dbt build {DBT_COMMON} --selector {config['selector']}"
            ),
        )
    return dag


for pipeline_config in json.loads(CONFIG_PATH.read_text(encoding="utf-8")):
    globals()[pipeline_config["dag_id"]] = make_dag(pipeline_config)
