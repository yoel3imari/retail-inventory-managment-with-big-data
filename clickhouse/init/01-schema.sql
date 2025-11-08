-- Retail Inventory Management Database Schema
-- Initialization script for ClickHouse

-- Create database
CREATE DATABASE IF NOT EXISTS retail;

-- Use the retail database
USE retail;

-- Dimension Tables

-- Date dimension table
CREATE TABLE IF NOT EXISTS dim_date (
    date_key Date,
    full_date Date,
    day_of_week UInt8,
    month UInt8,
    quarter UInt8,
    year UInt16,
    is_holiday UInt8,
    is_weekend UInt8
) ENGINE = Memory();

-- Product dimension table
CREATE TABLE IF NOT EXISTS dim_product (
    product_key String,
    sku String,
    product_name String,
    category String,
    sub_category String,
    brand String,
    supplier String,
    unit_cost Decimal(10,2),
    shelf_life_days Int32,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (product_key, category, brand);

-- Store dimension table
CREATE TABLE IF NOT EXISTS dim_store (
    store_key String,
    store_id String,
    store_name String,
    city String,
    region String,
    country String,
    square_footage Int32,
    store_type String,
    created_date DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (store_key, region, store_type);

-- Fact Tables

-- Sales fact table
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id String,
    date_key Date,
    product_key String,
    store_key String,
    quantity Int32,
    revenue Decimal(10,2),
    cost Decimal(10,2),
    profit Decimal(10,2),
    transaction_time DateTime,
    customer_id String,
    payment_method String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date_key)
ORDER BY (date_key, store_key, product_key, transaction_time);

-- Inventory fact table
CREATE TABLE IF NOT EXISTS fact_inventory (
    inventory_id String,
    date_key Date,
    product_key String,
    store_key String,
    quantity_on_hand Int32,
    reorder_point Int32,
    safety_stock Int32,
    last_updated DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date_key)
ORDER BY (date_key, store_key, product_key);

-- ML Predictions fact table
CREATE TABLE IF NOT EXISTS fact_ml_predictions (
    prediction_id String,
    date_key Date,
    product_key String,
    store_key String,
    predicted_demand Decimal(10,2),
    confidence_low Decimal(10,2),
    confidence_high Decimal(10,2),
    stock_out_risk_score Decimal(3,2),
    prediction_date DateTime DEFAULT now(),
    model_version String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date_key)
ORDER BY (date_key, store_key, product_key, prediction_date);

-- Raw Events Tables (for streaming data)

-- Raw sales events from Kafka
CREATE TABLE IF NOT EXISTS raw_sales_events (
    transaction_id String,
    store_id String,
    product_id String,
    quantity Int32,
    unit_price Decimal(10,2),
    total_amount Decimal(10,2),
    timestamp DateTime64(3),
    customer_id String,
    payment_method String,
    processed_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, store_id, product_id);

-- Raw inventory events from Kafka
CREATE TABLE IF NOT EXISTS raw_inventory_events (
    inventory_id String,
    store_id String,
    product_id String,
    quantity_change Int32,
    new_quantity Int32,
    reason String,
    timestamp DateTime64(3),
    processed_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, store_id, product_id);

-- Aggregated Views for Analytics

-- Daily sales summary view
CREATE VIEW IF NOT EXISTS daily_sales_summary AS
SELECT 
    date_key,
    store_key,
    product_key,
    SUM(quantity) as total_quantity,
    SUM(revenue) as total_revenue,
    SUM(profit) as total_profit,
    COUNT(DISTINCT sale_id) as transaction_count
FROM fact_sales
GROUP BY date_key, store_key, product_key;

-- Current inventory levels view
CREATE VIEW IF NOT EXISTS current_inventory AS
SELECT 
    store_key,
    product_key,
    quantity_on_hand,
    reorder_point,
    safety_stock,
    CASE 
        WHEN quantity_on_hand <= safety_stock THEN 'CRITICAL'
        WHEN quantity_on_hand <= reorder_point THEN 'LOW'
        ELSE 'NORMAL'
    END as stock_status,
    last_updated
FROM fact_inventory
WHERE (store_key, product_key, last_updated) IN (
    SELECT store_key, product_key, MAX(last_updated)
    FROM fact_inventory
    GROUP BY store_key, product_key
);

-- Product performance view
CREATE VIEW IF NOT EXISTS product_performance AS
SELECT 
    p.product_key,
    p.product_name,
    p.category,
    p.brand,
    SUM(s.quantity) as total_units_sold,
    SUM(s.revenue) as total_revenue,
    SUM(s.profit) as total_profit,
    (SUM(s.profit) / SUM(s.revenue)) * 100 as profit_margin_pct
FROM fact_sales s
JOIN dim_product p ON s.product_key = p.product_key
WHERE s.date_key >= today() - INTERVAL 30 DAY
GROUP BY p.product_key, p.product_name, p.category, p.brand;

-- Store performance view
CREATE VIEW IF NOT EXISTS store_performance AS
SELECT 
    s.store_key,
    s.store_name,
    s.region,
    s.store_type,
    COUNT(DISTINCT fs.sale_id) as total_transactions,
    SUM(fs.revenue) as total_revenue,
    SUM(fs.profit) as total_profit,
    AVG(fs.revenue) as avg_transaction_value
FROM fact_sales fs
JOIN dim_store s ON fs.store_key = s.store_key
WHERE fs.date_key >= today() - INTERVAL 7 DAY
GROUP BY s.store_key, s.store_name, s.region, s.store_type;

-- Low stock alerts view
CREATE VIEW IF NOT EXISTS low_stock_alerts AS
SELECT 
    s.store_name,
    p.product_name,
    p.category,
    i.quantity_on_hand,
    i.reorder_point,
    i.safety_stock,
    i.last_updated,
    CASE 
        WHEN i.quantity_on_hand <= i.safety_stock THEN 'CRITICAL'
        WHEN i.quantity_on_hand <= i.reorder_point THEN 'WARNING'
        ELSE 'NORMAL'
    END as alert_level
FROM current_inventory i
JOIN dim_store s ON i.store_key = s.store_key
JOIN dim_product p ON i.product_key = p.product_key
WHERE i.quantity_on_hand <= i.reorder_point;

-- ML predictions summary view
CREATE VIEW IF NOT EXISTS ml_predictions_summary AS
SELECT 
    s.store_name,
    p.product_name,
    p.category,
    mp.predicted_demand,
    mp.confidence_low,
    mp.confidence_high,
    mp.stock_out_risk_score,
    mp.prediction_date,
    mp.model_version
FROM fact_ml_predictions mp
JOIN dim_store s ON mp.store_key = s.store_key
JOIN dim_product p ON mp.product_key = p.product_key
WHERE mp.date_key >= today();

-- Insert sample date dimension data
INSERT INTO dim_date
SELECT 
    date as date_key,
    date as full_date,
    toDayOfWeek(date) as day_of_week,
    toMonth(date) as month,
    toQuarter(date) as quarter,
    toYear(date) as year,
    0 as is_holiday,  -- Simplified - would need holiday calendar
    if(toDayOfWeek(date) IN (6, 7), 1, 0) as is_weekend
FROM (
    SELECT toDate('2024-01-01') + number as date
    FROM numbers(365)  -- One year of dates
);

-- Print confirmation
SELECT 'Database schema created successfully' as status;