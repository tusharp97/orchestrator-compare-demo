{% macro cents_to_dollars(column_name, scale=2) %}
    round(cast({{ column_name }} as decimal(18, {{ scale + 2 }})) / 100, {{ scale }})
{% endmacro %}

{% macro completed_orders(relation) %}
    select *
    from {{ relation }}
    where status = 'completed'
      and amount >= {{ var('min_order_amount', 0) }}
{% endmacro %}
