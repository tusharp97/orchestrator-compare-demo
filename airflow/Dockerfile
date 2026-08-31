FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY airflow/dags /opt/airflow/dags
COPY dbt_project /opt/demo/dbt_project
COPY scripts/container /opt/demo/scripts

RUN mkdir -p /opt/demo/data /opt/demo/dbt_project/target /opt/demo/dbt_project/logs \
    && chown -R airflow:0 /opt/demo /opt/airflow/dags \
    && chmod -R g+rwX /opt/demo \
    && find /opt/demo/scripts -name '*.sh' -exec sed -i 's/\r$//' {} \; \
    && chmod +x /opt/demo/scripts/*.sh

# dbt cannot share Airflow 2.10's pip env: current dbt-adapters needs protobuf 6,
# while Airflow is pinned to protobuf 4. Isolate the CLI in its own venv.
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/dbt-venv/bin/pip install --no-cache-dir \
        dbt-core==1.9.8 \
        dbt-duckdb==1.9.2 \
        duckdb==1.2.2 \
    && chown -R airflow:0 /opt/dbt-venv

USER airflow
COPY airflow/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV PATH="/opt/dbt-venv/bin:${PATH}" \
    DBT_PROFILES_DIR=/opt/demo/dbt_project \
    DBT_PROJECT_DIR=/opt/demo/dbt_project \
    DEMO_DATA_DIR=/opt/demo/data \
    DUCKDB_PATH=/opt/demo/data/airflow.duckdb
