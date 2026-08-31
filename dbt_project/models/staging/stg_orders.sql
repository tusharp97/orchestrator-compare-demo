select
    cast(order_id as integer) as order_id,
    cast(customer_id as integer) as customer_id,
    cast(order_date as date) as order_date,
    {{ cents_to_dollars('amount_cents') }} as amount,
    lower(trim(status)) as status
from {{ ref('orders') }}
