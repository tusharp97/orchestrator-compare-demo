import json
import os
from pathlib import Path

import duckdb
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    ConfigurableResource,
    DailyPartitionsDefinition,
    Definitions,
    DynamicOut,
    DynamicOutput,
    MaterializeResult,
    RunRequest,
    ScheduleDefinition,
    SkipReason,
    asset,
    define_asset_job,
    in_process_executor,
    job,
    op,
    sensor,
)
from dagster_dbt import DbtCliResource, dbt_assets

PROJECT_DIR = Path(os.environ.get("DBT_PROJECT_DIR", "/opt/demo/dbt_project"))
DATA_DIR = Path(os.environ.get("DEMO_DATA_DIR", "/opt/demo/data"))
MANIFEST_PATH = PROJECT_DIR / "target" / "manifest.json"


class DuckDBResource(ConfigurableResource):
    database: str

    def connect(self, read_only: bool = True):
        return duckdb.connect(self.database, read_only=read_only)


@dbt_assets(manifest=MANIFEST_PATH)
def shop_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Expose dbt seeds and models as individually observable Dagster assets."""
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    deps=[AssetKey("fct_daily_revenue")],
    group_name="reporting",
    description="Publish the revenue mart as a portable JSON demo artifact.",
)
def daily_revenue_report(warehouse: DuckDBResource) -> MaterializeResult:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with warehouse.connect() as connection:
        rows = connection.execute(
            """
            select order_date, order_count, customer_count, gross_revenue
            from fct_daily_revenue
            order by order_date
            """
        ).fetchall()

    summary = {
        "orchestrator": "dagster",
        "database": warehouse.database,
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
    report_path = DATA_DIR / "dagster-summary.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return MaterializeResult(
        metadata={
            "report_path": str(report_path),
            "report_rows": len(rows),
            "gross_revenue_total": sum(float(row[3]) for row in rows),
        }
    )


daily_partitions = DailyPartitionsDefinition(
    start_date="2026-08-24",
    end_date="2026-08-27",
)


@asset(
    deps=[AssetKey("fct_daily_revenue")],
    partitions_def=daily_partitions,
    group_name="workshop",
    description="A partitioned JSON export for one business date.",
)
def daily_revenue_partition(
    context: AssetExecutionContext,
    warehouse: DuckDBResource,
) -> MaterializeResult:
    partition_date = context.partition_key
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with warehouse.connect() as connection:
        row = connection.execute(
            """
            select order_count, customer_count, gross_revenue
            from fct_daily_revenue
            where order_date = ?
            """,
            [partition_date],
        ).fetchone()

    payload = {
        "order_date": partition_date,
        "order_count": row[0] if row else 0,
        "customer_count": row[1] if row else 0,
        "gross_revenue": float(row[2]) if row else 0.0,
    }
    output = DATA_DIR / f"dagster-revenue-{partition_date}.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return MaterializeResult(
        metadata={
            "output": str(output),
            "partition_date": partition_date,
            "gross_revenue": payload["gross_revenue"],
        }
    )


shop_pipeline_job = define_asset_job(
    name="shop_revenue_pipeline",
    selection=AssetSelection.assets(
        AssetKey("daily_revenue_report")
    ).upstream(),
    description="Materialize the full seed-to-report asset graph.",
    executor_def=in_process_executor,
)

staging_assets_job = define_asset_job(
    name="staging_assets_job",
    selection=AssetSelection.assets(
        AssetKey("stg_customers"),
        AssetKey("stg_orders"),
    ).upstream(),
    executor_def=in_process_executor,
)

marts_assets_job = define_asset_job(
    name="marts_assets_job",
    selection=AssetSelection.assets(
        AssetKey("fct_daily_revenue"),
        AssetKey("daily_revenue_report"),
    ).upstream(),
    executor_def=in_process_executor,
)

partitioned_export_job = define_asset_job(
    name="partitioned_export_job",
    selection=AssetSelection.assets(AssetKey("daily_revenue_partition")),
    partitions_def=daily_partitions,
    executor_def=in_process_executor,
)


@op(out=DynamicOut(str))
def countries(warehouse: DuckDBResource):
    with warehouse.connect() as connection:
        rows = connection.execute(
            "select distinct country from int_completed_orders order by country"
        ).fetchall()
    for (country,) in rows:
        yield DynamicOutput(country, mapping_key=country.lower())


@op
def country_revenue(context, country: str, warehouse: DuckDBResource) -> dict:
    with warehouse.connect() as connection:
        row = connection.execute(
            """
            select count(distinct order_id), coalesce(sum(amount), 0)
            from int_completed_orders
            where country = ?
            """,
            [country],
        ).fetchone()
    result = {
        "country": country,
        "order_count": row[0],
        "gross_revenue": float(row[1]),
    }
    context.log.info("Country result: %s", result)
    return result


@job(executor_def=in_process_executor)
def dynamic_country_job():
    countries().map(country_revenue)


every_five_minutes = ScheduleDefinition(
    name="shop_revenue_every_five_minutes",
    job=shop_pipeline_job,
    cron_schedule="*/5 * * * *",
    execution_timezone="UTC",
)

hourly_marts = ScheduleDefinition(
    name="hourly_marts",
    job=marts_assets_job,
    cron_schedule="0 * * * *",
    execution_timezone="UTC",
)


@sensor(job=shop_pipeline_job, minimum_interval_seconds=30)
def ready_file_sensor(context):
    marker = DATA_DIR / "dagster-ready.flag"
    if not marker.exists():
        return SkipReason(f"Waiting for {marker}")

    modified = str(marker.stat().st_mtime_ns)
    if context.cursor == modified:
        return SkipReason("Ready file has already been processed")

    context.update_cursor(modified)
    return RunRequest(run_key=modified)


defs = Definitions(
    assets=[shop_dbt_assets, daily_revenue_report, daily_revenue_partition],
    jobs=[
        shop_pipeline_job,
        staging_assets_job,
        marts_assets_job,
        partitioned_export_job,
        dynamic_country_job,
    ],
    schedules=[every_five_minutes, hourly_marts],
    sensors=[ready_file_sensor],
    resources={
        "dbt": DbtCliResource(
            project_dir=str(PROJECT_DIR),
            profiles_dir=str(PROJECT_DIR),
        ),
        "warehouse": DuckDBResource(database=os.environ["DUCKDB_PATH"]),
    },
)
