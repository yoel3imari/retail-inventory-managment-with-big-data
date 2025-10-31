-- Create database
CREATE DATABASE IF NOT EXISTS retail;

-- Products table
CREATE TABLE IF NOT EXISTS retail.products
(
    product_id String,
    product_name String,
    category String,
    brand String,
    unit_price Decimal(10, 2),
    cost_price Decimal(10, 2),
    supplier_id String,
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (category, product_id)
PARTITION BY toYYYYMM(created_at);

-- Inventory levels table
CREATE TABLE IF NOT EXISTS retail.inventory
(
    inventory_id String,
    product_id String,
    store_id String,
    warehouse_id String,
    quantity_on_hand Int32,
    quantity_reserved Int32,
    quantity_available Int32,
    reorder_point Int32,
    reorder_quantity Int32,
    last_updated DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(last_updated)
ORDER BY (store_id, product_id)
PARTITION BY toYYYYMM(last_updated);

-- Sales transactions table (from Kafka stream)
CREATE TABLE IF NOT EXISTS retail.sales
(
    transaction_id String,
    product_id String,
    store_id String,
    quantity_sold Int32,
    unit_price Decimal(10, 2),
    discount_amount Decimal(10, 2),
    total_amount Decimal(10, 2),
    payment_method String,
    customer_id String,
    transaction_time DateTime,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (transaction_time, store_id, product_id)
PARTITION BY toYYYYMM(transaction_time);

-- Stock movements table
CREATE TABLE IF NOT EXISTS retail.stock_movements
(
    movement_id String,
    product_id String,
    from_location String,
    to_location String,
    movement_type String, -- 'PURCHASE', 'SALE', 'TRANSFER', 'ADJUSTMENT', 'RETURN'
    quantity Int32,
    movement_time DateTime,
    reason String,
    user_id String,
    inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
ORDER BY (movement_time, product_id)
PARTITION BY toYYYYMM(movement_time);

-- Stores table
CREATE TABLE IF NOT EXISTS retail.stores
(
    store_id String,
    store_name String,
    store_type String, -- 'RETAIL', 'WAREHOUSE', 'ONLINE'
    city String,
    region String,
    country String,
    square_meters Int32,
    opened_date Date,
    is_active Boolean
)
ENGINE = MergeTree()
ORDER BY store_id;

-- Materialized view for daily inventory summary
CREATE MATERIALIZED VIEW IF NOT EXISTS retail.daily_inventory_summary
ENGINE = SummingMergeTree()
ORDER BY (date, store_id, product_id)
AS
SELECT
    toDate(last_updated) as date,
    store_id,
    product_id,
    argMax(quantity_on_hand, last_updated) as quantity_on_hand,
    argMax(quantity_available, last_updated) as quantity_available
FROM retail.inventory
GROUP BY date, store_id, product_id;

-- Materialized view for hourly sales metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS retail.hourly_sales_metrics
ENGINE = SummingMergeTree()
ORDER BY (date_hour, store_id, product_id)
AS
SELECT
    toStartOfHour(transaction_time) as date_hour,
    store_id,
    product_id,
    count() as transaction_count,
    sum(quantity_sold) as total_quantity,
    sum(total_amount) as total_revenue,
    avg(unit_price) as avg_price
FROM retail.sales
GROUP BY date_hour, store_id, product_id;

-- View for low stock alerts
CREATE VIEW IF NOT EXISTS retail.low_stock_alerts AS
SELECT
    i.product_id,
    p.product_name,
    p.category,
    i.store_id,
    i.quantity_available,
    i.reorder_point,
    i.reorder_quantity,
    (i.reorder_point - i.quantity_available) as shortage
FROM retail.inventory i
JOIN retail.products p ON i.product_id = p.product_id
WHERE i.quantity_available < i.reorder_point
ORDER BY shortage DESC;

-- View for product performance
CREATE VIEW IF NOT EXISTS retail.product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    count(DISTINCT s.transaction_id) as total_transactions,
    sum(s.quantity_sold) as total_units_sold,
    sum(s.total_amount) as total_revenue,
    sum(s.total_amount) / sum(s.quantity_sold) as avg_selling_price,
    p.cost_price,
    (sum(s.total_amount) - (sum(s.quantity_sold) * p.cost_price)) as total_profit,
    ((sum(s.total_amount) - (sum(s.quantity_sold) * p.cost_price)) / sum(s.total_amount)) * 100 as profit_margin_pct
FROM retail.products p
LEFT JOIN retail.sales s ON p.product_id = s.product_id
WHERE s.transaction_time >= now() - INTERVAL 30 DAY
GROUP BY p.product_id, p.product_name, p.category, p.brand, p.cost_price
ORDER BY total_revenue DESC;