# Additional workshop and production topics

The current workshop deliberately runs on one machine and one DuckDB database
per orchestrator. The following additions can extend it without obscuring the
core Airflow-versus-Dagster comparison.

## dbt additions

* Model contracts with enforced column data types.
* Source freshness and loaded-at checks against a real ingestion table.
* `state:modified+` Slim CI using a saved production manifest.
* Deferral to production relations during pull-request validation.
* A local dbt package and package-level macros.
* Semantic models, metrics, and MetricFlow.
* Custom materializations.
* Python models on an adapter that supports them.
* Seeds versus real external sources.
* Grants, persist-docs, pre-hooks, and warehouse-specific configurations.
* Elementary or another dbt observability package.
* Multiple targets representing development, test, and production.

## Airflow additions

* Custom timetables for business calendars and market holidays.
* Deferrable operators and triggerer service.
* KubernetesExecutor or KubernetesPodOperator.
* CeleryExecutor, queues, pools, and priority weights.
* Task groups and nested visual organization.
* Dynamic task mapping over API-discovered data.
* REST API triggering from CI/CD.
* OpenLineage integration.
* Secrets Manager or Vault connection backend.
* Teams, Slack, PagerDuty, or email notification callbacks.
* SLA/deadline alerts and data-quality gates.
* Cross-DAG dependencies using assets rather than TriggerDagRun.
* Backfill, catchup, rerun, and idempotency failure exercises.
* A custom provider, hook, and operator.
* Multi-tenant DAG ownership and role-based access.

## Dagster additions

* Automation conditions for declarative asset reconciliation.
* Freshness policies and freshness checks.
* Multi-dimensional and dynamic partitions.
* Partition mappings between differently partitioned assets.
* Asset sensors triggered by upstream materializations.
* Observable source assets for externally managed data.
* IO managers for DuckDB, Snowflake, S3, or object storage.
* Dagster Pipes for external Python or Kubernetes workloads.
* Multiple code locations to demonstrate team isolation.
* Run queues, concurrency pools, and retry policies.
* Asset checks beyond dbt tests.
* Resources configured differently by deployment environment.
* Backfill policies and large-partition backfill strategies.
* GraphQL API automation.
* Dagster Cloud deployment and branch deployments.

## Shared platform additions

* Replace DuckDB with Snowflake, PostgreSQL, or BigQuery.
* MinIO for local S3-compatible ingestion and file assets.
* Kafka or Redpanda for streaming/event demonstrations.
* OpenTelemetry traces plus Prometheus and Grafana dashboards.
* OpenLineage/Marquez for a tool-neutral lineage comparison.
* Great Expectations, Soda, or Collate for external data quality.
* Vault or LocalStack Secrets Manager for secret injection.
* A fake REST API with pagination, retries, and rate limiting.
* Fault-injection labs: malformed input, timeout, duplicate event, and partial
  write.
* CI that builds images, validates Airflow DAG imports, parses dbt, loads
  Dagster definitions, and executes smoke tests.
* ARM64 and AMD64 multi-platform image builds.
* Image signing, SBOM generation, and vulnerability scanning.

## Production decision exercises

* Define workload inventory: scheduled, event-driven, human approval, and
  long-running operations.
* Score operator/integration coverage.
* Compare asset-aware versus task-aware observability.
* Estimate migration effort from coarse dbt commands to model-level assets.
* Test tenancy, isolation, secrets, and blast radius.
* Benchmark scheduler throughput and backfill behavior.
* Compare managed offerings and total operating cost.
* Define exit criteria and use the same failure scenarios for both products.

## Prefect, Kestra, and Argo

Prefect and Kestra are in this repo as optional Compose profiles (`prefect`,
`kestra`) and as steps in `./scripts/demo.sh tour`. They use distinct host
ports (4200 and 8082).

Argo Workflows is still a future item: add a kind/k3d profile only on a
16 GB+ machine. Do not share host ports with Airflow (8080) or dbt docs
(8081) if you add it later (Argo Server commonly uses 2746).
