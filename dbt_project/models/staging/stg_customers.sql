select
    cast(customer_id as integer) as customer_id,
    trim(customer_name) as customer_name,
    upper(trim(country)) as country
from {{ ref('customers') }}
