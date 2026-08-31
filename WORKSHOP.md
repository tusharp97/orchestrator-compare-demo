# Extended Airflow, Dagster, and dbt workshop

This workshop takes approximately 2.5 hours. Everything runs in Docker. Start
the environment before the session:

```bash
./scripts/demo.sh up
```

Open these tabs:

* Airflow: <http://localhost:8080> (`admin` / `admin`)
* Dagster: <http://localhost:3000>
* dbt Docs: <http://localhost:8081>
* Prefect (optional / tour): <http://localhost:4200>
* Kestra (optional / tour): <http://localhost:8082>

The startup script runs the baseline pipelines and verifies that summaries
total `612.00`. On an 8 GB Mac use `./scripts/demo.sh tour` instead of `up`.
Prefect is http://localhost:4200 and Kestra is http://localhost:8082; those
ports are never reused by Airflow or dbt docs.

## Agenda

| Time | Module |
| --- | --- |
| 0:00–0:15 | Architecture and task graphs versus asset graphs |
| 0:15–0:45 | dbt project structure and reusable SQL |
| 0:45–1:10 | dbt testing, selectors, snapshots, and incremental models |
| 1:10–1:20 | Break |
| 1:20–1:50 | Airflow scheduling and dynamic orchestration |
| 1:50–2:20 | Dagster assets, jobs, sensors, and partitions |
| 2:20–2:35 | Side-by-side labs |
| 2:35–2:45 | Selection guidance and future extensions |

## Module 1 — The shared data pipeline

Both orchestrators run the same graph:

```text
customers + orders
        ↓
stg_customers + stg_orders
        ↓
int_completed_orders
        ↓
fct_daily_revenue
        ↓
JSON report
```

Airflow expresses the execution order as tasks. Dagster reads the dbt manifest
and exposes durable datasets as assets.

## Module 2 — dbt fundamentals and advanced features

Use the Dagster container as a Docker-only dbt CLI:

```bash
docker compose exec dagster dbt ls \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project
```

### Macros and variables

Review:

* `macros/money.sql`
* `macros/generic_tests.sql`
* `macros/hooks.sql`
* `vars` and `on-run-end` in `dbt_project.yml`

Run with a different minimum order:

```bash
docker compose exec dagster dbt build \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project \
  --vars '{"min_order_amount": 100}'
```

Reset to the default by running the normal full job from Dagster.

### Selectors and tags

```bash
docker compose exec dagster dbt ls \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project \
  --selector staging

docker compose exec dagster dbt build \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project \
  --selector marts
```

Review `selectors.yml`: staging, marts, nightly, and a CI teaching selector.

### Tests

The project includes:

* built-in `not_null`, `unique`, and `relationships` data tests;
* custom generic `positive_value` tests;
* a singular test that rejects cancelled completed orders;
* a dbt unit test for daily aggregation.

Run only tests:

```bash
docker compose exec dagster dbt test \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project
```

### Incremental model

`fct_daily_revenue` uses `delete+insert` with `order_date` as its unique key.
Run it twice and compare the first full creation with the second incremental
execution:

```bash
docker compose exec dagster dbt run \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project \
  --select fct_daily_revenue+
```

### Snapshots

Run the customer snapshot, then change a customer in the seed and repeat seed
plus snapshot to demonstrate historical versions:

```bash
docker compose exec dagster dbt snapshot \
  --project-dir /opt/demo/dbt_project \
  --profiles-dir /opt/demo/dbt_project
```

### Documentation and exposures

Open dbt Docs on port 8081. Show lineage, column tests, the dashboard exposure,
model ownership, and documentation blocks.

## Module 3 — Airflow orchestration patterns

All workshop DAGs are paused initially. Enable only the DAG currently being
demonstrated to avoid concurrent writes to the Airflow DuckDB file.

### Baseline cron DAG

`shop_revenue_pipeline` runs every five minutes:

```text
seed → dbt run → dbt test → publish summary
```

Discuss retries, catchup, task logs, and DAG-run history.

### Metadata-generated DAGs

Open:

* `workshop_dbt_staging`
* `workshop_dbt_marts`
* `workshop_dbt_nightly`

All three are generated from `workshop_pipelines.json`. Additions require a
metadata record rather than another copied DAG module.

### Dataset scheduling

Enable `workshop_dataset_consumer`, then manually trigger
`workshop_dataset_producer`. The producer emits an Airflow Dataset event and
the consumer runs without a cron expression.

### TaskFlow, parameters, branching, and mapping

Trigger `workshop_taskflow_mapping` with:

```json
{
  "countries": ["UK", "US"]
}
```

The DAG:

1. branches based on whether transformed data exists;
2. reads runtime parameters;
3. dynamically maps one task per country;
4. joins mapped and no-data paths with a trigger rule.

### Sensors and parent/child DAGs

Trigger `workshop_dataset_producer` to create the marker file, then trigger
`workshop_master_sensor`.

The master:

1. waits in reschedule mode for a file;
2. triggers `workshop_dbt_marts`;
3. waits for the child DAG;
4. invokes success or failure callbacks.

## Module 4 — Dagster orchestration patterns

### Asset graph

Open **Assets** and inspect dbt seeds, models, tests, and the JSON report. dbt
tests appear as asset checks.

### Asset-selection jobs

Run:

* `staging_assets_job` — staging assets plus upstream seeds;
* `marts_assets_job` — the mart/report selection plus upstream assets;
* `shop_revenue_pipeline` — the baseline report and all dependencies.

This demonstrates selective materialization without maintaining separate DAG
definitions.

### Schedules

Under **Overview → Schedules**, compare:

* `shop_revenue_every_five_minutes`;
* `hourly_marts`.

Enable one schedule at a time during the workshop.

### Partitions and backfills

Open `daily_revenue_partition`, select a date from 2026-08-24 through
2026-08-26, and materialize it. Then launch a backfill across all partitions.
Each partition writes an independently addressable JSON artifact.

### Sensor

Enable `ready_file_sensor`, then create its event:

```bash
echo ready > data/dagster-ready.flag
```

The sensor records the file modification timestamp as its cursor, producing
exactly one run per file update.

### Dynamic graph

Run `dynamic_country_job`. The `countries` op returns dynamic outputs and
Dagster creates one `country_revenue` step for every country found in DuckDB.

### Resource injection

Review `DuckDBResource`. Assets and ops request the resource as a typed
function parameter instead of constructing infrastructure configuration
throughout the code.

## Module 5 — Side-by-side exercises

### Exercise A: run only marts

* Airflow: trigger `workshop_dbt_marts` (`dbt --selector marts`).
* Dagster: run `marts_assets_job`.

Discuss CLI selection versus native asset selection.

### Exercise B: fan out by country

* Airflow: run `workshop_taskflow_mapping`.
* Dagster: run `dynamic_country_job`.

Compare mapped task instances with dynamic outputs.

### Exercise C: event-driven execution

* Airflow: producer emits a Dataset event.
* Dagster: update `data/dagster-ready.flag`.

Compare event semantics, cursor state, and observability.

### Exercise D: backfill

* Airflow: discuss logical dates and DAG-run backfills.
* Dagster: backfill the three `daily_revenue_partition` partitions.

## Workshop cleanup

```bash
./scripts/demo.sh clean
```

On Windows:

```powershell
.\scripts\demo.ps1 clean
```
