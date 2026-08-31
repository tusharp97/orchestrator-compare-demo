# Orchestrator compare demo

**Moving this to another computer?** Open [START_HERE.md](START_HERE.md). Copy
this whole folder; on the Docker machine run `./scripts/demo.sh up` or, on an
8 GB Mac, `./scripts/demo.sh tour`. Do not install Python or orchestrators on
the host.

A portable Docker-only comparison of Airflow, Dagster, Prefect, and Kestra
running the same dbt project against DuckDB. Argo Workflows is documented only:
it needs Kubernetes and does not fit an 8 GB laptop.

## Requirements

- Docker Desktop with Docker Compose **v2.13 or newer** (the scripts use
  `docker compose run --build`). Check with `docker compose version`.
- Ports below must be free. Each product keeps its **own** host port even when
  you run stacks one at a time.

| Service | Host port | When it starts |
| --- | --- | --- |
| Airflow | **8080** | `up`, `airflow`, `tour` |
| Dagster | **3000** | `up`, `dagster`, `tour` |
| dbt Docs | **8081** | `up`, `docs` |
| Prefect | **4200** | `prefect`, `tour` |
| Kestra | **8082** | `kestra`, `tour` |

Do not install Python, Airflow, Dagster, Prefect, Kestra, dbt, DuckDB, or
PostgreSQL on the host.

### RAM

| Command | What runs together | Docker RAM |
| --- | --- | --- |
| `up` | Airflow + Dagster + dbt docs | about **6 GB** |
| `airflow` / `dagster` / `prefect` / `kestra` | One stack | about **3.5–4.5 GB** |
| `tour` | One stack at a time, then stop | same as one stack |
| All UIs at once | not supported | too large for 8 GB |

An **8 GB Mac** should use `tour` or a single-tool command. Give Docker Desktop
about **4 GB**. Close extra browsers before starting.

## Start

macOS/Linux:

```bash
chmod +x scripts/demo.sh
./scripts/demo.sh up          # Airflow + Dagster + docs
./scripts/demo.sh tour        # 8 GB: one orchestrator at a time
./scripts/demo.sh tour --no-wait
```

Windows PowerShell:

```powershell
.\scripts\demo.ps1 up
.\scripts\demo.ps1 tour
.\scripts\demo.ps1 tour -NoWait
```

Single-tool commands stop any other demo stack first, then start one UI:

```bash
./scripts/demo.sh airflow
./scripts/demo.sh dagster
./scripts/demo.sh prefect
./scripts/demo.sh kestra
./scripts/demo.sh docs
```

The first build downloads images and can take several minutes. Each stack runs
the shop-revenue pipeline once and checks that the JSON total is `612.00`.
Compose waits for each service's healthcheck before the pipeline runs, so the
scripts never poll or sleep.

Run `./scripts/demo.sh help` (or `.\scripts\demo.ps1 help`) for the full
command list.

| Service | URL | Credentials |
| --- | --- | --- |
| Airflow | http://localhost:8080 | `admin` / `admin` |
| Dagster | http://localhost:3000 | none |
| dbt Docs | http://localhost:8081 | none |
| Prefect | http://localhost:4200 | none |
| Kestra | http://localhost:8082 | none |

`tour` pauses after each tool (unless `--no-wait`) so you can open that UI
before the script stops it and starts the next one.

## What the bootstrap run does

The same dbt graph runs on every orchestrator: seed → run → test → JSON
summary. Cancelled `$200` is excluded. Expected total is `612.00`.

Each orchestrator uses its own DuckDB file:

- `data/airflow.duckdb`
- `data/dagster.duckdb`
- `data/prefect.duckdb`
- `data/kestra.duckdb`

Successful runs also produce matching `data/<tool>-summary.json` files.

## Workshop coverage

- **dbt:** macros, variables, hooks, selectors, tags, groups, incremental
  models, snapshots, documentation, exposures, analyses, generic tests,
  singular tests, and unit tests.
- **Airflow:** cron scheduling, metadata-generated DAGs, Dataset scheduling,
  TaskFlow, runtime params, branching, dynamic task mapping, sensors,
  parent/child DAGs, retries, trigger rules, and callbacks.
- **Dagster:** dbt assets and checks, asset-selection jobs, schedules, sensors,
  daily partitions/backfills, dynamic outputs, and typed resources.
- **Prefect:** Python flow with the same dbt steps, visible in the OSS UI.
- **Kestra:** YAML flow with the same dbt steps, visible in the OSS UI.

### Airflow

1. Open http://localhost:8080 and select `shop_revenue_pipeline`.
2. Click **Trigger DAG** for another live run.
3. Inspect `load_seed_data`, `transform_with_dbt`, `test_with_dbt`, and
   `publish_summary`.

This pipeline is a control-flow graph: seed, transform, test, then publish.

### Dagster

1. Open http://localhost:3000 and select **Assets**.
2. Select all assets and click **Materialize selected**.
3. Inspect lineage from seeds through `fct_daily_revenue` to
   `daily_revenue_report`.

This pipeline is a data graph: dbt seeds and models are individually visible
assets.

### Prefect

1. Open http://localhost:4200 after `./scripts/demo.sh prefect` or during
   `tour`.
2. Open the `shop-revenue-pipeline` flow run and inspect the four tasks.

### Kestra

1. Open http://localhost:8082 after `./scripts/demo.sh kestra` or during
   `tour`.
2. Open namespace `demo`, flow `shop_revenue_pipeline`, and the latest
   execution.

## Useful commands

```bash
./scripts/demo.sh status
./scripts/demo.sh logs
./scripts/demo.sh down
./scripts/demo.sh clean
```

`clean` removes containers, named volumes, generated DuckDB databases, and
summary files. It leaves the source code and seed CSVs untouched.

## Architecture

```text
customers.csv ─┐
               ├─ dbt staging ── fct_daily_revenue ── JSON report
orders.csv ────┘

Airflow:  scheduled task DAG  → dbt CLI → DuckDB   (port 8080)
Dagster: scheduled asset job  → dagster-dbt → DuckDB (port 3000)
Prefect: Python flow          → dbt CLI → DuckDB   (port 4200)
Kestra:  YAML tasks           → dbt CLI → DuckDB   (port 8082)
```

DuckDB is only the demo warehouse. Airflow and Kestra store metadata in their
own PostgreSQL containers. Prefect Server uses a SQLite database in a named
volume. Dagster stores run history in a named volume.

Kestra also listens on container port `8081` for its management/health
endpoint. That port is deliberately **not** published, so it cannot collide
with dbt docs on host `8081`.

Learning paths:

- [PRESENTATION.md](PRESENTATION.md) — 30-minute comparison
- [WORKSHOP.md](WORKSHOP.md) — extended hands-on workshop
- [FUTURE_ENHANCEMENTS.md](FUTURE_ENHANCEMENTS.md) — additional topics

Argo Workflows is not started here. It is a Kubernetes controller; a local
kind/k3d cluster needs more RAM than this demo targets.

## Troubleshooting

- **Docker is missing:** install Docker Desktop only.
- **A port is in use:** stop the program using that port. Do not remap two
  orchestrators onto the same host port.
- **8 GB machine feels frozen:** use `tour` or a single-tool command; do not
  run `up`.
- **Apple Silicon:** selected base images publish `linux/arm64` variants.
- **A stale or partial first startup:** run `clean` and then start again.
- **Corporate proxy/certificate errors:** Docker must trust the corporate CA.
- **Airflow image pip conflict (`protobuf` / `dbt-adapters`):** dbt is installed
  in `/opt/dbt-venv` inside the Airflow image, not in Airflow's own
  environment. Rebuild with
  `docker compose --profile airflow build --no-cache airflow-webserver`.
