import os

import duckdb
import pendulum
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule


@dag(
    dag_id="workshop_taskflow_mapping",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=True,
    params={
        "countries": Param(
            ["UK", "US"],
            type="array",
            items={"type": "string"},
            description="Countries expanded into parallel mapped tasks.",
        )
    },
    tags=["workshop", "taskflow", "branching", "dynamic-mapping", "params"],
)
def taskflow_mapping():
    @task.branch
    def choose_branch() -> str:
        database = os.environ["DUCKDB_PATH"]
        try:
            with duckdb.connect(database, read_only=True) as connection:
                count = connection.execute(
                    "select count(*) from int_completed_orders"
                ).fetchone()[0]
        except duckdb.Error:
            count = 0
        return "get_countries" if count else "no_data"

    @task
    def get_countries(**context) -> list[str]:
        return context["params"]["countries"]

    @task
    def summarize_country(country: str) -> dict:
        database = os.environ["DUCKDB_PATH"]
        with duckdb.connect(database, read_only=True) as connection:
            row = connection.execute(
                """
                select count(distinct order_id), coalesce(sum(amount), 0)
                from int_completed_orders
                where country = ?
                """,
                [country],
            ).fetchone()
        return {
            "country": country,
            "order_count": row[0],
            "gross_revenue": float(row[1]),
        }

    branch = choose_branch()
    countries = get_countries()
    mapped_summaries = summarize_country.expand(country=countries)
    no_data = EmptyOperator(task_id="no_data")
    done = EmptyOperator(
        task_id="done",
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    branch >> [countries, no_data]
    countries >> mapped_summaries
    [mapped_summaries, no_data] >> done


taskflow_mapping()
