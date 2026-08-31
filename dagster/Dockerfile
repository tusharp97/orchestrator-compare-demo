FROM python:3.11-slim

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY dagster/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /opt/demo
COPY dbt_project /opt/demo/dbt_project
COPY dagster /opt/demo/dagster_code
COPY scripts/container /opt/demo/scripts

ENV DBT_PROFILES_DIR=/opt/demo/dbt_project \
    DBT_PROJECT_DIR=/opt/demo/dbt_project \
    DEMO_DATA_DIR=/opt/demo/data \
    DUCKDB_PATH=/tmp/dagster-build.duckdb

RUN dbt parse --project-dir /opt/demo/dbt_project --profiles-dir /opt/demo/dbt_project \
    && mkdir -p /opt/demo/dagster_home /opt/demo/data \
    && find /opt/demo/scripts -name '*.sh' -exec sed -i 's/\r$//' {} \; \
    && chmod +x /opt/demo/scripts/*.sh

ENV DUCKDB_PATH=/opt/demo/data/dagster.duckdb \
    DAGSTER_HOME=/opt/demo/dagster_home

ENTRYPOINT ["/opt/demo/scripts/dagster-entrypoint.sh"]
