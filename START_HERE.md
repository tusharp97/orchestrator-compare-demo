# Copy this folder to the Docker machine

This project is self-contained. You do not need Cursor, Python, Airflow,
Dagster, Prefect, Kestra, or dbt on the other computer. You only need Docker
Desktop.

## 1. Copy

Copy the whole `orchestrator-compare-demo` directory (zip, USB, git clone, or
cloud drive). Keep the folder structure intact.

## 2. On the machine with Docker

**16 GB+ RAM** (Airflow and Dagster together):

```bash
cd orchestrator-compare-demo
chmod +x scripts/demo.sh
./scripts/demo.sh up
```

**8 GB RAM** (one orchestrator at a time):

```bash
./scripts/demo.sh tour
```

`tour` starts Airflow, waits for Enter, stops it, then Dagster, Prefect, and
Kestra. Each UI keeps a **different** port: 8080, 3000, 4200, 8082.

The first run downloads container images and can take several minutes. Each
stack runs the shop-revenue pipeline once and checks that the total is
`612.00`.

## 3. Open the UIs

| App | URL | Login | Port is exclusive to |
| --- | --- | --- | --- |
| Airflow | http://localhost:8080 | `admin` / `admin` | Airflow |
| Dagster | http://localhost:3000 | none | Dagster |
| dbt Docs | http://localhost:8081 | none | dbt docs (`up` or `docs`) |
| Prefect | http://localhost:4200 | none | Prefect |
| Kestra | http://localhost:8082 | none | Kestra |

Give Docker Desktop about **4 GB** on an 8 GB Mac. Do not run `up` on 8 GB.

## 4. Present

Follow `PRESENTATION.md` for the 30-minute talk or `WORKSHOP.md` for the
extended hands-on session. On 8 GB, walk the Prefect and Kestra UIs during the
`tour` pauses.

## Stop / reset

```bash
./scripts/demo.sh down     # stop containers
./scripts/demo.sh clean    # stop and delete volumes/output files
```

If something fails, run `clean` and then start again. Check Docker Desktop is
running and that the ports in the table above are free.
