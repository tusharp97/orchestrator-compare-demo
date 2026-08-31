#!/usr/bin/env bash
set -euo pipefail

mkdir -p /opt/demo/data /tmp/dbt-target /tmp/dbt-logs
chmod 777 /opt/demo/data /tmp/dbt-target /tmp/dbt-logs || true

if [[ $# -eq 0 ]]; then
  echo "Airflow command required" >&2
  exit 2
fi

exec airflow "$@"
