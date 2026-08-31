FROM prefecthq/prefect:3-python3.11

RUN pip install --no-cache-dir \
    dbt-core==1.9.8 \
    dbt-duckdb==1.9.2 \
    duckdb==1.2.2

WORKDIR /opt/demo
COPY dbt_project /opt/demo/dbt_project
COPY prefect /opt/demo/prefect_code
COPY scripts/container /opt/demo/scripts

ENV DBT_PROFILES_DIR=/opt/demo/dbt_project \
    DBT_PROJECT_DIR=/opt/demo/dbt_project \
    DEMO_DATA_DIR=/opt/demo/data \
    DUCKDB_PATH=/opt/demo/data/prefect.duckdb \
    ORCHESTRATOR=prefect

RUN mkdir -p /opt/demo/data /tmp/dbt-target /tmp/dbt-logs \
    && find /opt/demo/scripts -name '*.sh' -exec sed -i 's/\r$//' {} \; \
    && chmod +x /opt/demo/scripts/*.sh

ENTRYPOINT []
CMD ["python", "/opt/demo/prefect_code/shop_pipeline.py"]
