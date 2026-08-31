#!/usr/bin/env bash
set -euo pipefail

mkdir -p /opt/demo/data /opt/demo/dagster_home /tmp/dbt-target /tmp/dbt-logs
chmod 777 /opt/demo/data || true
cp /opt/demo/dagster_code/dagster.yaml /opt/demo/dagster_home/dagster.yaml

if [[ $# -gt 0 ]]; then
  exec "$@"
fi

exec dagster dev -h 0.0.0.0 -p 3000 -f /opt/demo/dagster_code/definitions.py
