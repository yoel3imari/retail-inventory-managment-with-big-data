-- Enhanced ClickHouse Schema for Retail Inventory Management
-- Additional tables and views to support Spark streaming and ML applications

USE retail;

-- Additional tables for real-time analytics

-- Real-time sales metrics table (populated by Spark streaming)
CREATE TABLE IF NOT EXISTS realtime_sales_metrics (
    window_start DateTime64(3),
    window_end DateTime64(3),
    store_id String,
    product_id String,
    total_quantity AggregateFunction(sum, Int32),
    total_revenue AggregateFunction(sum, Decimal(10,2)),
    transaction_count AggregateFunction(count, String),
    unique_customers AggregateFunction(uniq, String),
    avg_unit_price AggregateFunction(avg, Decimal(10,2)),
    processing_timestamp DateTime DEFAULT now()
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(window_start)
ORDER BY (window_start, store_id, product_id);

-- Real-time inventory alerts table (populated by Spark streaming)
CREATE TABLE IF NOT EXISTS realtime_inventory_alerts (
    alert_id String,
    store_id String,
    product_id String,
    alert_type Enum8('LOW_STOCK' = 1, 'OUT_OF_STOCK' = 2, 'RAPID_DEPLETION' = 3, 'OVERSTOCKED' = 4),
    alert_severity Enum8('INFO' = 1, 'LOW' = 2, 'MEDIUM' = 3, 'HIGH' = 4, 'CRITICAL' = 5),
    current_stock Int32,
    reorder_point Int32,
    stock_change Int32,
    stock_change_rate Decimal(5,2),
    alert_timestamp DateTime64(3),
    processed_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(alert_timestamp)
ORDER BY (alert_timestamp, store_id, product_id, alert_severity);

-- ML model training results table
CREATE TABLE IF NOT EXISTS ml_model_results (
    model_id String,
    model_type Enum8('DEMAND_FORECASTING' = 1, 'STOCK_OPTIMIZATION' = 2, 'ANOMALY_DETECTION' = 3),
    training_date Date,
    model_metrics String,  -- JSON string with metrics like RMSE, accuracy, etc.
    feature_importance String,  -- JSON string with feature importance
    model_path String,  -- Path to saved model file
    training_duration_seconds Int32,
    training_data_size Int64,
    model_version String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(training_date)
ORDER BY (training_date, model_type, model_version);

-- Batch processing results table
CREATE TABLE IF NOT EXISTS batch_processing_results (
    batch_id String,
    processing_date Date,
    processing_type Enum8('DAILY_REPORT' = 1, 'WEEKLY_ANALYSIS' = 2, 'MONTHLY_SUMMARY' = 3),
    total_records_processed Int64,
    processing_duration_seconds Int32,
    kpis_json String,  -- JSON string with calculated KPIs
    top_products_json String,  -- JSON string with top performing products
    top_stores_json String,  -- JSON string with top performing stores
    inventory_health_metrics String,  -- JSON string with inventory health
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(processing_date)
ORDER BY (processing_date, processing_type);

-- Enhanced views for analytics

-- Real-time dashboard view
CREATE VIEW IF NOT EXISTS realtime_dashboard AS
SELECT 
    store_id,
    product_id,
    sum(total_quantity) as total_quantity,
    sum(total_revenue) as total_revenue,
    count(transaction_count) as transaction_count,
    uniq(unique_customers) as unique_customers,
    avg(avg_unit_price) as avg_unit_price,
    max(processing_timestamp) as last_updated
FROM realtime_sales_metrics
GROUP BY store_id, product_id;

-- Active alerts view
CREATE VIEW IF NOT EXISTS active_alerts AS
SELECT 
    s.store_name,
    p.product_name,
    p.category,
    a.alert_type,
    a.alert_severity,
    a.current_stock,
    a.reorder_point,
    a.stock_change,
    a.stock_change_rate,
    a.alert_timestamp
FROM realtime_inventory_alerts a
JOIN dim_store s ON a.store_id = s.store_key
JOIN dim_product p ON a.product_id = p.product_key
WHERE a.alert_timestamp >= now() - INTERVAL 1 HOUR
ORDER BY a.alert_severity DESC, a.alert_timestamp DESC;

-- ML model performance view
CREATE VIEW IF NOT EXISTS ml_model_performance AS
SELECT 
    model_type,
    model_version,
    training_date,
    JSONExtractString(model_metrics, 'rmse') as rmse,
    JSONExtractString(model_metrics, 'accuracy') as accuracy,
    JSONExtractString(model_metrics, 'precision') as precision,
    JSONExtractString(model_metrics, 'recall') as recall,
    training_duration_seconds,
    training_data_size,
    created_at
FROM ml_model_results
ORDER BY training_date DESC, model_type;

-- Inventory turnover analysis view
CREATE VIEW IF NOT EXISTS inventory_turnover_analysis AS
SELECT 
    s.store_name,
    p.product_name,
    p.category,
    AVG(i.quantity_on_hand) as avg_stock_level,
    SUM(CASE WHEN fs.quantity > 0 THEN fs.quantity ELSE 0 END) as total_sold,
    (SUM(CASE WHEN fs.quantity > 0 THEN fs.quantity ELSE 0 END) / 
     NULLIF(AVG(i.quantity_on_hand), 0)) as turnover_ratio,
    COUNT(DISTINCT fs.date_key) as days_with_sales
FROM fact_inventory i
JOIN dim_store s ON i.store_key = s.store_key
JOIN dim_product p ON i.product_key = p.product_key
LEFT JOIN fact_sales fs ON i.store_key = fs.store_key AND i.product_key = fs.product_key
WHERE i.date_key >= today() - INTERVAL 30 DAY
  AND fs.date_key >= today() - INTERVAL 30 DAY
GROUP BY s.store_name, p.product_name, p.category
HAVING total_sold > 0 AND avg_stock_level > 0;

-- Customer behavior analysis view
CREATE VIEW IF NOT EXISTS customer_behavior_analysis AS
SELECT 
    customer_id,
    COUNT(DISTINCT date_key) as shopping_days,
    SUM(quantity) as total_items_purchased,
    SUM(revenue) as total_spent,
    AVG(revenue) as avg_transaction_value,
    MIN(transaction_time) as first_purchase_date,
    MAX(transaction_time) as last_purchase_date,
    COUNT(DISTINCT store_key) as stores_visited,
    COUNT(DISTINCT product_key) as unique_products_purchased,
    arrayDistinct(groupArray(payment_method)) as payment_methods_used
FROM fact_sales
WHERE date_key >= today() - INTERVAL 90 DAY
GROUP BY customer_id
HAVING total_spent > 0;

-- Seasonal sales patterns view
CREATE VIEW IF NOT EXISTS seasonal_sales_patterns AS
SELECT 
    d.month,
    d.day_of_week,
    d.is_weekend,
    p.category,
    s.region,
    COUNT(fs.sale_id) as transaction_count,
    SUM(fs.quantity) as total_quantity,
    SUM(fs.revenue) as total_revenue,
    AVG(fs.revenue) as avg_transaction_value
FROM fact_sales fs
JOIN dim_date d ON fs.date_key = d.date_key
JOIN dim_product p ON fs.product_key = p.product_key
JOIN dim_store s ON fs.store_key = s.store_key
WHERE d.date_key >= today() - INTERVAL 365 DAY
GROUP BY 
    d.month,
    d.day_of_week,
    d.is_weekend,
    p.category,
    s.region
ORDER BY d.month, d.day_of_week, p.category;

-- Store comparison view
CREATE VIEW IF NOT EXISTS store_comparison AS
SELECT 
    s.store_name,
    s.region,
    s.store_type,
    s.square_footage,
    COUNT(DISTINCT fs.customer_id) as unique_customers,
    COUNT(fs.sale_id) as total_transactions,
    SUM(fs.revenue) as total_revenue,
    SUM(fs.profit) as total_profit,
    AVG(fs.revenue) as avg_transaction_value,
    (SUM(fs.revenue) / s.square_footage) as revenue_per_sqft,
    (COUNT(fs.sale_id) / s.square_footage) as transactions_per_sqft
FROM fact_sales fs
JOIN dim_store s ON fs.store_key = s.store_key
WHERE fs.date_key >= today() - INTERVAL 30 DAY
GROUP BY 
    s.store_name,
    s.region,
    s.store_type,
    s.square_footage
ORDER BY revenue_per_sqft DESC;

-- Product category performance view
CREATE VIEW IF NOT EXISTS category_performance AS
SELECT 
    p.category,
    p.sub_category,
    COUNT(DISTINCT fs.store_key) as stores_selling,
    COUNT(DISTINCT fs.customer_id) as unique_customers,
    SUM(fs.quantity) as total_units_sold,
    SUM(fs.revenue) as total_revenue,
    SUM(fs.profit) as total_profit,
    (SUM(fs.profit) / SUM(fs.revenue)) * 100 as profit_margin_pct,
    AVG(fs.quantity) as avg_units_per_transaction,
    COUNT(fs.sale_id) as total_transactions
FROM fact_sales fs
JOIN dim_product p ON fs.product_key = p.product_key
WHERE fs.date_key >= today() - INTERVAL 30 DAY
GROUP BY p.category, p.sub_category
ORDER BY total_revenue DESC;

-- Insert sample data for enhanced tables (for testing)

-- Insert sample ML model results
INSERT INTO ml_model_results VALUES
(
    'model_001',
    'DEMAND_FORECASTING',
    today(),
    '{"rmse": "12.45", "accuracy": "0.89", "precision": "0.87", "recall": "0.91"}',
    '{"demand_lag_7": 0.25, "day_of_week": 0.18, "category": 0.15, "store_region": 0.12}',
    '/models/demand_forecasting_v1',
    3600,
    150000,
    'v1.0',
    now()
),
(
    'model_002', 
    'STOCK_OPTIMIZATION',
    today(),
    '{"rmse": "8.23", "accuracy": "0.92", "precision": "0.90", "recall": "0.94"}',
    '{"total_sales": 0.32, "stock_volatility": 0.21, "avg_price": 0.15, "sales_count": 0.12}',
    '/models/stock_optimization_v1',
    2400,
    120000,
    'v1.0',
    now()
);

-- Insert sample batch processing results
INSERT INTO batch_processing_results VALUES
(
    'batch_001',
    today(),
    'DAILY_REPORT',
    150000,
    120,
    '{"total_revenue": 125000.50, "total_transactions": 2500, "total_customers": 1800, "avg_transaction_value": 50.20}',
    '{"top_products": [{"product_name": "Premium Headphones", "revenue": 12500}, {"product_name": "Smart Watch", "revenue": 9800}]}',
    '{"top_stores": [{"store_name": "Downtown Flagship", "revenue": 25000}, {"store_name": "Mall Location", "revenue": 22000}]}',
    '{"out_of_stock_rate": 2.5, "low_stock_rate": 8.7, "avg_stock_level": 45.2}',
    now()
);

-- Print confirmation
SELECT 'Enhanced schema created successfully' as status;