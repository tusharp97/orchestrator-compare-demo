FROM kestra/kestra:v0.22.46

USER root

# dbt lives in its own virtualenv so the install works on any base image,
# including ones that enforce PEP 668 for the system interpreter.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        python3 \
        python3-venv \
        curl \
        ca-certificates \
    && python3 -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/dbt-venv/bin/pip install --no-cache-dir \
        dbt-core==1.9.8 \
        dbt-duckdb==1.9.2 \
        duckdb==1.2.2 \
    && rm -rf /var/lib/apt/lists/*

COPY dbt_project /opt/demo/dbt_project
COPY kestra/flows /opt/demo/kestra/flows
COPY scripts/container /opt/demo/scripts

RUN mkdir -p /opt/demo/data /tmp/dbt-target /tmp/dbt-logs /tmp/kestra-wd/tmp \
    && find /opt/demo/scripts -name '*.sh' -exec sed -i 's/\r$//' {} \; \
    && chmod +x /opt/demo/scripts/*.sh
