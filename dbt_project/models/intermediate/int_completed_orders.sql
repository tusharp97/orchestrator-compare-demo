with completed as (
    {{ completed_orders(ref('stg_orders')) }}
)

select
    completed.order_id,
    completed.order_date,
    completed.amount,
    customers.customer_id,
    customers.customer_name,
    customers.country
from completed
inner join {{ ref('stg_customers') }} as customers
    on completed.customer_id = customers.customer_id
