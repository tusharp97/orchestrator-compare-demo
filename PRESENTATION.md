# 30-minute presentation guide

Install only Docker Desktop. On a 16 GB+ machine, run `./scripts/demo.sh up`
before the meeting so Airflow, Dagster, and dbt docs are ready. On an **8 GB
Mac**, run `./scripts/demo.sh tour` and use the Enter pauses to show one UI at
a time. Ports stay unique: Airflow 8080, Dagster 3000, dbt docs 8081, Prefect
4200, Kestra 8082.

For selectors, snapshots, dynamic DAG factories, Dataset scheduling, sensors,
dynamic mapping, partitions, and hands-on labs, use `WORKSHOP.md`.

## 0:00–3:00 — Frame the comparison

- Both products run exactly the same CSV inputs and dbt project.
- dbt owns SQL transformations and tests.
- The orchestrator owns scheduling, retries, dependencies, execution history,
  and observability.
- Each orchestrator writes its own DuckDB file under `data/`
  (`airflow`, `dagster`, `prefect`, `kestra`).

Key question: **Are we primarily orchestrating tasks or data assets?**

## 3:00–8:00 — Explain the dbt project

Open `dbt_project/models`:

1. `stg_customers` normalizes customer data.
2. `stg_orders` casts dates and monetary values.
3. `fct_daily_revenue` joins both inputs and excludes cancelled orders.
4. `schema.yml` applies uniqueness, non-null, and relationship tests.

Expected result:

- 2026-08-24: 2 orders, 200.50
- 2026-08-25: 1 order, 40.25
- 2026-08-26: 2 orders, 371.25
- Total: 612.00

Stress that the SQL is unchanged between orchestrators.

## 8:00–17:00 — Airflow

Open http://localhost:8080 and trigger `shop_revenue_pipeline`.

Show:

1. **Code:** four explicit tasks connected with `>>`.
2. **Grid view:** each task instance belongs to a DAG run.
3. **Logs:** the dbt command and test results.
4. **Schedule:** `*/5 * * * *`, `catchup=False`, retries.
5. **Result:** `data/airflow-summary.json`.

Talking points:

- The graph expresses control flow: do A, then B, then C.
- `dbt run` is one Airflow task even though dbt contains multiple models.
- Airflow excels for mixed operational work: APIs, Kubernetes pods, branching,
  notifications, and external systems.
- A green DAG means the declared tasks succeeded.

Ask: “Which table is stale?” Traditional task-oriented orchestration does not
make that the primary UI concept.

## 17:00–27:00 — Dagster

Open http://localhost:3000, go to Assets, select all, and materialize.

Show:

1. **Asset graph:** seeds, staging models, fact table, JSON report.
2. **Selective execution:** choose `fct_daily_revenue` with upstream assets.
3. **Materialization metadata:** report rows and total revenue.
4. **Run timeline and dbt logs.**
5. **Schedule:** enable `shop_revenue_every_five_minutes`.

Talking points:

- An asset represents durable data: a table, file, model, or report.
- Dagster reads dbt's manifest, so each dbt node is visible without manually
  reproducing its dependencies.
- The same platform also has jobs and ops for imperative workflows.
- Partitions, freshness, and targeted backfills build on the asset model.

Ask: “Which dataset is stale?” This is the question Dagster is designed to
answer.

## 27:00–31:00 — Comparison and recommendation

Airflow:

- Best default for heterogeneous task and control-flow orchestration.
- Broader provider/operator ecosystem.
- Familiar DAG-run and task-instance operational model.
- Coarse dbt invocation is straightforward.

Dagster:

- Best when datasets and dbt models are the primary graph.
- First-class lineage, materializations, partitions, and selective backfills.
- Strong local Python development and resource injection.
- Requires teams to adopt asset-oriented design to realize its benefits.

For current DPv2-style execution—metadata-driven ingestion, coarse dbt runs,
child workflows, APIs, and Kubernetes jobs—Airflow remains the safer default.
For a redesigned warehouse platform where dbt models and datasets are operated
as individual assets, Dagster deserves a proof of concept.

## Optional 5-minute extension

- Edit one order amount in `dbt_project/seeds/orders.csv`.
- Rebuild the images: `docker compose up --build --detach`.
- Re-run only the relevant Dagster asset selection.
- Contrast this with triggering or clearing tasks in the Airflow DAG.

This extension brings the session to approximately 35 minutes.

## Optional: Prefect and Kestra (8 GB tour)

During `./scripts/demo.sh tour`, after Airflow and Dagster:

1. **Prefect** (http://localhost:4200) — Python `@flow` / `@task` wrapping the
   same dbt CLI steps. Emphasize a lightweight OSS control plane.
2. **Kestra** (http://localhost:8082) — YAML tasks for the same steps.
   Emphasize a declarative, UI-friendly OSS orchestrator.

Do not start these while Airflow and Dagster are still running on 8 GB RAM.
Argo Workflows is omitted: it requires Kubernetes.
