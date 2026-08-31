select
    country,
    count(distinct order_id) as order_count,
    round(sum(amount), 2) as gross_revenue
from {{ ref('int_completed_orders') }}
where (
    '{{ var("demo_country", "ALL") }}' = 'ALL'
    or country = '{{ var("demo_country") }}'
)
group by country
order by gross_revenue desc
