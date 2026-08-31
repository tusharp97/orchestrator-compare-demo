{% macro log_workshop_run() %}
    {% do log(
        "Workshop run complete: target=" ~ target.name
        ~ ", schemas=" ~ schemas | join(","),
        info=True
    ) %}
    {{ return("select 1") }}
{% endmacro %}
