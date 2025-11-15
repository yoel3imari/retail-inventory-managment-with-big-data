-- ClickHouse Kafka Integration
-- This script sets up direct Kafka integration to bypass Spark compatibility issues

-- Drop existing tables if they exist
DROP TABLE IF EXISTS retail.kafka_sales_raw;
DROP TABLE IF EXISTS retail.kafka_inventory_raw;
DROP TABLE IF EXISTS retail.kafka_sales_mv;
DROP TABLE IF EXISTS retail.kafka_inventory_mv;
DROP TABLE IF EXISTS retail.kafka_tables_info;

-- Create Kafka tables that consume directly from Kafka topics
-- Using the correct topic names: retail-sales-transactions and retail-inventory-updates
CREATE TABLE IF NOT EXISTS retail.kafka_sales_raw (
    sale_id String,
    product_id String,
    store_id String,
    quantity Int32,
    price Decimal64(2),
    timestamp DateTime64(3)
) ENGINE = Kafka(
    'kafka:19092',
    'retail-sales-transactions',
    'clickhouse-sales-consumer-group',
    'JSONEachRow'
) SETTINGS
    kafka_thread_per_consumer = 0,
    kafka_num_consumers = 1,
    kafka_skip_broken_messages = 100,
    kafka_max_block_size = 1048576;

CREATE TABLE IF NOT EXISTS retail.kafka_inventory_raw (
    inventory_id String,
    product_id String,
    store_id String,
    quantity Int32,
    timestamp DateTime64(3)
) ENGINE = Kafka(
    'kafka:19092',
    'retail-inventory-updates',
    'clickhouse-inventory-consumer-group',
    'JSONEachRow'
) SETTINGS
    kafka_thread_per_consumer = 0,
    kafka_num_consumers = 1,
    kafka_skip_broken_messages = 100,
    kafka_max_block_size = 1048576;

-- Create materialized views to populate the actual tables
-- Note: We need to map the incoming data to the target table schema
CREATE MATERIALIZED VIEW IF NOT EXISTS retail.kafka_sales_mv TO retail.fact_sales AS
SELECT 
    sale_id,
    toDate(timestamp) AS date_key,
    product_id AS product_key,
    store_id AS store_key,
    quantity,
    price AS revenue,
    0.0 AS cost,
    price AS profit,
    timestamp AS transaction_time,
    '' AS customer_id,
    'cash' AS payment_method
FROM retail.kafka_sales_raw;

-- Create materialized view for inventory with proper column mapping
CREATE MATERIALIZED VIEW IF NOT EXISTS retail.kafka_inventory_mv TO retail.fact_inventory AS
SELECT 
    inventory_id,
    toDate(timestamp) AS date_key,
    product_id AS product_key,
    store_id AS store_key,
    quantity AS quantity_on_hand,
    10 AS reorder_point,  -- Default value
    5 AS safety_stock,    -- Default value
    timestamp AS last_updated
FROM retail.kafka_inventory_raw;

-- Create views for monitoring Kafka consumption (simplified)
CREATE VIEW IF NOT EXISTS retail.kafka_tables_info AS
SELECT 
    name,
    engine,
    create_table_query
FROM system.tables 
WHERE database = 'retail' AND engine = 'Kafka';