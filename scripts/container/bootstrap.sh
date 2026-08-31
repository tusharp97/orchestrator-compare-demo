#!/usr/bin/env bash
set -euo pipefail

mkdir -p /opt/demo/data /tmp/bootstrap-dagster-home /tmp/dbt-target /tmp/dbt-logs
chmod 777 /opt/demo/data || true
if [[ -f /opt/demo/dagster_code/dagster.yaml ]]; then
  cp /opt/demo/dagster_code/dagster.yaml /tmp/bootstrap-dagster-home/dagster.yaml
fi

IFS=',' read -r -a TOOLS <<< "${BOOTSTRAP_TOOLS:-airflow,dagster}"

wait_for() {
  local name="$1"
  local url="$2"
  local extra=("${@:3}")
  echo "Waiting for ${name} at ${url}"
  for _ in $(seq 1 90); do
    if curl -sf --max-time 5 "${extra[@]}" "$url" >/dev/null; then
      echo "${name} is ready"
      return 0
    fi
    sleep 4
  done
  echo "${name} did not become ready" >&2
  return 1
}

bootstrap_airflow() {
  local airflow_url="${AIRFLOW_URL:-http://airflow-webserver:8080}"
  wait_for "Airflow webserver" "${airflow_url}/health"
  wait_for "Airflow DAG" "${airflow_url}/api/v1/dags/shop_revenue_pipeline" -u admin:admin

  echo "Triggering Airflow DAG"
  curl -sf -u admin:admin \
    -X POST "${airflow_url}/api/v1/dags/shop_revenue_pipeline/dagRuns" \
    -H "Content-Type: application/json" \
    -d "{\"conf\":{}}" >/tmp/airflow-trigger.json

  python - <<'PY'
import json, time, urllib.request, base64, os, sys

airflow = os.environ.get("AIRFLOW_URL", "http://airflow-webserver:8080")
auth = base64.b64encode(b"admin:admin").decode()

def get(path):
    req = urllib.request.Request(
        airflow + path,
        headers={"Authorization": f"Basic {auth}"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)

for _ in range(60):
    payload = get("/api/v1/dags/shop_revenue_pipeline/dagRuns?order_by=-start_date&limit=1")
    runs = payload.get("dag_runs") or []
    if not runs:
        time.sleep(5)
        continue
    state = runs[0]["state"]
    print(f"Airflow run {runs[0]['dag_run_id']} state={state}", flush=True)
    if state == "success":
        break
    if state == "failed":
        sys.exit("Airflow pipeline failed")
    time.sleep(5)
else:
    sys.exit("Airflow pipeline did not finish")
PY
}

bootstrap_dagster() {
  local dagster_url="${DAGSTER_URL:-http://dagster:3000}"
  wait_for "Dagster" "${dagster_url}/server_info"
  echo "Executing Dagster job"
  export DAGSTER_HOME=/tmp/bootstrap-dagster-home
  export DUCKDB_PATH=/opt/demo/data/dagster.duckdb
  export DBT_PROJECT_DIR=/opt/demo/dbt_project
  export DBT_PROFILES_DIR=/opt/demo/dbt_project
  export DEMO_DATA_DIR=/opt/demo/data
  dagster job execute -f /opt/demo/dagster_code/definitions.py -j shop_revenue_pipeline
}

bootstrap_kestra() {
  python3 /opt/demo/scripts/bootstrap_kestra.py
}

for tool in "${TOOLS[@]}"; do
  tool="${tool// /}"
  case "$tool" in
    airflow) bootstrap_airflow ;;
    dagster) bootstrap_dagster ;;
    kestra) bootstrap_kestra ;;
    prefect)
      echo "Prefect is executed by the prefect-run service, not bootstrap.sh"
      ;;
    "")
      ;;
    *)
      echo "Unknown BOOTSTRAP_TOOLS entry: ${tool}" >&2
      exit 2
      ;;
  esac
done

python3 /opt/demo/scripts/verify_summary.py "${TOOLS[@]}"
echo "Bootstrap pipelines succeeded"
