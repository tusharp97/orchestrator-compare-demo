{{
    config(
        materialized='incremental',
        unique_key='order_date',
        incremental_strategy='delete+insert'
    )
}}

with enriched as (
    select *
    from {{ ref('int_completed_orders') }}
    {% if is_incremental() %}
    where order_date >= (
        select coalesce(max(order_date), date '1900-01-01')
        from {{ this }}
    )
    {% endif %}
)

select
    order_date,
    count(distinct order_id) as order_count,
    count(distinct customer_id) as customer_count,
    round(sum(amount), 2) as gross_revenue
from enriched
group by order_date
