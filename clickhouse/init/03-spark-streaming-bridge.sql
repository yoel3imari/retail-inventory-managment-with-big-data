-- Spark Streaming Bridge Tables for Kafka to ClickHouse Data Pipeline
-- This schema creates tables specifically for Spark streaming applications

USE retail;

-- Unified streaming events table for raw Kafka events
CREATE TABLE IF NOT EXISTS streaming_events_raw (
    event_id String,
    event_type Enum8('SALES' = 1, 'INVENTORY' = 2, 'CUSTOMER' = 3, 'PRICE_CHANGE' = 4),
    event_timestamp DateTime64(3),
    kafka_timestamp DateTime64(3),
    store_id String,
    product_id String,
    payload String,  -- Raw JSON payload
    processed_at DateTime DEFAULT now(),
    processing_batch String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (event_timestamp, event_type, store_id, product_id);

-- Real-time sales metrics for Spark streaming (aggregated)
CREATE TABLE IF NOT EXISTS spark_sales_metrics (
    window_start DateTime64(3),
    window_end DateTime64(3),
    store_id String,
    product_id String,
    total_quantity Int32,
    total_revenue Decimal(10,2),
    transaction_count Int32,
    unique_customers Int32,
    avg_unit_price Decimal(10,2),
    processing_timestamp DateTime DEFAULT now(),
    spark_job_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(window_start)
ORDER BY (window_start, store_id, product_id);

-- Real-time inventory metrics for Spark streaming
CREATE TABLE IF NOT EXISTS spark_inventory_metrics (
    window_start DateTime64(3),
    window_end DateTime64(3),
    store_id String,
    product_id String,
    latest_stock Int32,
    min_stock Int32,
    max_stock Int32,
    reorder_level Int32,
    update_count Int32,
    stock_status Enum8('IN_STOCK' = 1, 'LOW_STOCK' = 2, 'OUT_OF_STOCK' = 3),
    stock_percentage Decimal(5,2),
    processing_timestamp DateTime DEFAULT now(),
    spark_job_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(window_start)
ORDER BY (window_start, store_id, product_id);

-- Spark streaming alerts table
CREATE TABLE IF NOT EXISTS spark_streaming_alerts (
    alert_id String,
    alert_type Enum8('LOW_STOCK' = 1, 'OUT_OF_STOCK' = 2, 'RAPID_DEPLETION' = 3, 
                     'SALES_SPIKE' = 4, 'PRICE_ANOMALY' = 5, 'INVENTORY_ANOMALY' = 6),
    alert_severity Enum8('INFO' = 1, 'LOW' = 2, 'MEDIUM' = 3, 'HIGH' = 4, 'CRITICAL' = 5),
    store_id String,
    product_id String,
    current_value Decimal(15,2),
    threshold_value Decimal(15,2),
    alert_message String,
    alert_timestamp DateTime64(3),
    processing_timestamp DateTime DEFAULT now(),
    spark_job_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(alert_timestamp)
ORDER BY (alert_timestamp, alert_severity, store_id, product_id);

-- Spark job monitoring table
CREATE TABLE IF NOT EXISTS spark_job_monitoring (
    job_id String,
    job_name String,
    start_time DateTime,
    end_time DateTime,
    status Enum8('RUNNING' = 1, 'COMPLETED' = 2, 'FAILED' = 3, 'STOPPED' = 4),
    records_processed Int64,
    processing_duration_seconds Int32,
    error_message String,
    checkpoint_location String,
    last_updated DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_time)
ORDER BY (start_time, job_name, status);

-- Views for monitoring the Spark streaming bridge

-- Real-time dashboard view for Spark streaming metrics
CREATE VIEW IF NOT EXISTS spark_streaming_dashboard AS
SELECT 
    'SALES' as metric_type,
    store_id,
    product_id,
    total_quantity,
    total_revenue,
    transaction_count,
    unique_customers,
    window_start,
    window_end
FROM spark_sales_metrics
WHERE window_start >= now() - INTERVAL 1 HOUR

UNION ALL

SELECT 
    'INVENTORY' as metric_type,
    store_id,
    product_id,
    latest_stock as total_quantity,
    0 as total_revenue,
    update_count as transaction_count,
    0 as unique_customers,
    window_start,
    window_end
FROM spark_inventory_metrics
WHERE window_start >= now() - INTERVAL 1 HOUR;

-- Active alerts view
CREATE VIEW IF NOT EXISTS spark_active_alerts AS
SELECT 
    s.store_name,
    p.product_name,
    a.alert_type,
    a.alert_severity,
    a.current_value,
    a.threshold_value,
    a.alert_message,
    a.alert_timestamp
FROM spark_streaming_alerts a
JOIN dim_store s ON a.store_id = s.store_key
JOIN dim_product p ON a.product_id = p.product_key
WHERE a.alert_timestamp >= now() - INTERVAL 1 HOUR
ORDER BY a.alert_severity DESC, a.alert_timestamp DESC;

-- Spark job status view
CREATE VIEW IF NOT EXISTS spark_job_status AS
SELECT 
    job_name,
    status,
    records_processed,
    processing_duration_seconds,
    start_time,
    end_time,
    last_updated
FROM spark_job_monitoring
WHERE last_updated >= now() - INTERVAL 1 DAY
ORDER BY last_updated DESC;

-- Data quality metrics view
CREATE VIEW IF NOT EXISTS spark_data_quality AS
SELECT 
    event_type,
    count(*) as total_events,
    countIf(payload != '') as valid_payloads,
    countIf(payload = '') as empty_payloads,
    min(event_timestamp) as earliest_event,
    max(event_timestamp) as latest_event,
    avg(dateDiff('second', event_timestamp, processed_at)) as avg_processing_lag_seconds
FROM streaming_events_raw
WHERE event_timestamp >= today()
GROUP BY event_type;

-- Insert sample monitoring data
INSERT INTO spark_job_monitoring VALUES
(
    'job_001',
    'sales_streaming',
    now() - INTERVAL 30 MINUTE,
    now(),
    'COMPLETED',
    15000,
    1800,
    '',
    '/tmp/checkpoint/sales_streaming',
    now()
),
(
    'job_002', 
    'inventory_streaming',
    now() - INTERVAL 25 MINUTE,
    now(),
    'RUNNING',
    8000,
    1500,
    '',
    '/tmp/checkpoint/inventory_streaming',
    now()
);

-- Print confirmation
SELECT 'Spark streaming bridge tables created successfully' as status;