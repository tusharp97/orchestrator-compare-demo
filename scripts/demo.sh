#!/usr/bin/env bash
# Portable orchestrator demo launcher. Works with bash 3.2 (stock macOS bash).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

usage() {
  cat <<'EOF'
Usage: ./scripts/demo.sh <command> [--no-wait]

  up         Airflow + Dagster + dbt docs together (needs ~6 GB Docker RAM)
  airflow    Only Airflow            http://localhost:8080  (admin/admin)
  dagster    Only Dagster            http://localhost:3000
  prefect    Only Prefect            http://localhost:4200
  kestra     Only Kestra             http://localhost:8082
  docs       Only dbt docs           http://localhost:8081
  tour       Each orchestrator one at a time (the 8 GB RAM path)
  status     Show demo containers
  logs       Follow logs of running demo containers
  down       Stop every demo stack
  clean      Stop every stack and delete volumes and generated files

Options:
  --no-wait  In "tour", do not pause for Enter between tools

Every product keeps its own host port, so nothing is reused:
  Airflow 8080 | Dagster 3000 | dbt docs 8081 | Prefect 4200 | Kestra 8082
EOF
}

COMMAND=""
NO_WAIT=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-wait)
      NO_WAIT=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -z "$COMMAND" ]; then
        COMMAND="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
  shift
done
COMMAND="${COMMAND:-up}"

if [ "$COMMAND" = "help" ]; then
  usage
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop, then rerun this script." >&2
  echo "Nothing is installed on the host except what Docker Desktop provides." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

mkdir -p data
chmod 777 data 2>/dev/null || true

ALL_PROFILES="--profile airflow --profile airflow-run --profile dagster --profile dagster-run --profile docs --profile prefect --profile prefect-run --profile kestra --profile kestra-run --profile verify"

compose_all() {
  # shellcheck disable=SC2086
  docker compose $ALL_PROFILES "$@"
}

stop_all() {
  compose_all down --remove-orphans "$@"
}

print_urls() {
  case "$1" in
    airflow) echo "Airflow:  http://localhost:8080  (admin/admin)" ;;
    dagster) echo "Dagster:  http://localhost:3000" ;;
    prefect) echo "Prefect:  http://localhost:4200" ;;
    kestra)  echo "Kestra:   http://localhost:8082" ;;
    docs)    echo "dbt Docs: http://localhost:8081" ;;
    up)
      echo "Airflow:  http://localhost:8080  (admin/admin)"
      echo "Dagster:  http://localhost:3000"
      echo "dbt Docs: http://localhost:8081"
      ;;
  esac
}

# Compose starts each *-run service's dependencies and waits for their
# healthchecks, so the script never polls for readiness itself.
start_stack() {
  case "$1" in
    airflow)
      docker compose --profile airflow --profile airflow-run \
        run --rm --build airflow-run
      ;;
    dagster)
      docker compose --profile dagster --profile dagster-run \
        run --rm --build dagster-run
      ;;
    prefect)
      docker compose --profile prefect --profile prefect-run \
        run --rm --build prefect-run
      ;;
    kestra)
      docker compose --profile kestra --profile kestra-run \
        run --rm --build kestra-run
      ;;
    docs)
      docker compose --profile docs up \
        --build --detach --wait --wait-timeout 600 dbt-docs
      ;;
    *)
      echo "Unknown stack: $1" >&2
      exit 2
      ;;
  esac
}

pause_between() {
  if [ "$NO_WAIT" -eq 1 ]; then
    return 0
  fi
  if [ ! -t 0 ]; then
    echo "No terminal attached; continuing without a pause after $1."
    return 0
  fi
  printf 'Press Enter to stop %s and continue to the next tool... ' "$1"
  read -r _ignored || true
}

case "$COMMAND" in
  up)
    stop_all >/dev/null 2>&1 || true
    docker compose --profile airflow --profile dagster --profile verify \
      run --rm --build bootstrap
    docker compose --profile docs up \
      --build --detach --wait --wait-timeout 600 dbt-docs
    echo
    print_urls up
    echo "Summary files are in ./data (each total is 612.00)."
    echo "On an 8 GB machine use: ./scripts/demo.sh tour"
    ;;
  airflow|dagster|prefect|kestra|docs)
    stop_all >/dev/null 2>&1 || true
    start_stack "$COMMAND"
    echo
    print_urls "$COMMAND"
    if [ "$COMMAND" != "docs" ]; then
      echo "Summary file: ./data/${COMMAND}-summary.json"
    fi
    echo "Stop it with: ./scripts/demo.sh down"
    ;;
  tour)
    stop_all >/dev/null 2>&1 || true
    for tool in airflow dagster prefect kestra; do
      echo
      echo "=============================================="
      echo " ${tool}"
      echo "=============================================="
      start_stack "$tool"
      echo
      print_urls "$tool"
      pause_between "$tool"
      stop_all
    done
    echo
    echo "Tour finished. Only one stack ran at a time."
    echo "Summary files left in ./data:"
    echo "  airflow-summary.json  dagster-summary.json"
    echo "  prefect-summary.json  kestra-summary.json"
    ;;
  status)
    compose_all ps
    ;;
  logs)
    compose_all logs --follow
    ;;
  down)
    stop_all
    ;;
  clean)
    stop_all --volumes
    rm -f data/*.duckdb data/*-summary.json data/dagster-revenue-*.json
    echo "Removed containers, volumes, DuckDB files, and summaries."
    ;;
  *)
    echo "Unknown command: $COMMAND" >&2
    usage >&2
    exit 2
    ;;
esac
