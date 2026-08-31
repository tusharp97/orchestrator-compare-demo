{% snapshot customers_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols=['customer_name', 'country']
    )
}}

select * from {{ ref('stg_customers') }}

{% endsnapshot %}
