select completed.*
from {{ ref('int_completed_orders') }} as completed
inner join {{ ref('stg_orders') }} as orders
    on completed.order_id = orders.order_id
where orders.status = 'cancelled'
