{% docs revenue_mart %}
The daily revenue mart contains completed shop orders only. It demonstrates
macro-based money conversion, reusable filtering, incremental processing,
generic tests, singular tests, and orchestration by Airflow and Dagster.
{% enddocs %}

{% docs orchestration_comparison %}
Airflow invokes dbt selectors as tasks. Dagster reads the dbt manifest and
represents dbt nodes as software-defined assets.
{% enddocs %}
